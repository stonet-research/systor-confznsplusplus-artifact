#include "./zns.h"
#include <math.h>
#include <signal.h>

#define ZNS_EXTERNAL_PAGE_SIZE (4 * KiB)  // Exposed through NVMe
#define ZNS_INTERNAL_PAGE_SIZE (8 * KiB) // Internal mapped size, the flash page size
#define ZNS_PAGE_PARALLELISM (ZNS_INTERNAL_PAGE_SIZE / ZNS_EXTERNAL_PAGE_SIZE) // How much parallel I/O fits in one flash page
#define ZNS_ZASL_SIZE_BYTES (1 * MiB)
#define ZNS_ZONE_SIZE_BYTES (2 * GiB)
#define ZNS_ZONE_SIZE_PAGES (ZNS_ZONE_SIZE_BYTES / ZNS_INTERNAL_PAGE_SIZE)
//#define FINISH_BLOCK_SIZE ((ZNS_INTERNAL_PAGE_SIZE / 512ULL) * 64ULL)
#define FINISH_BLOCK_SIZE ((ZNS_INTERNAL_PAGE_SIZE / 512ULL) * 1ULL)
uint64_t lag = 0;
uint64_t finishing = 0;

struct zns_zone_reset_ctx {
    NvmeRequest *req;
    NvmeZone    *zone;
};

static uint64_t zns_advance_status(FemuCtrl *n, NvmeNamespace *ns, NvmeCmd *cmd, NvmeRequest *req);

// Get the logical zone that the application sees
static inline uint32_t zns_get_logical_zone_idx(NvmeNamespace *ns, uint64_t slba)
{
    FemuCtrl *ctrl = ns->ctrl;
    return ctrl->zone_size_log2 > 0 ? slba >> ctrl->zone_size_log2 : slba / ctrl->zone_size;
}

// Get the internal zone assigned by our simple vtable
static inline uint32_t zns_get_physical_zone_idx(NvmeNamespace *ns, uint64_t slba)
{
    uint32_t logical_zone_idx = zns_get_logical_zone_idx(ns, slba);
    if (ns->ctrl->zvtable->entries[logical_zone_idx].physical_zone == NULL) {
        // femu_err("Get physical_idx when NULL\n");
        return 0;
    }
    uint64_t trueslba = ns->ctrl->zvtable->entries[logical_zone_idx].physical_zone->w_ptr;
    return zns_get_logical_zone_idx(ns, trueslba);
}

// Get LUN of the address
static inline uint64_t zns_get_ppn_idx(NvmeNamespace *ns, uint64_t slba) 
{
    FemuCtrl *ctrl = ns->ctrl;
    uint64_t zone_pages = ZNS_ZONE_SIZE_PAGES;
    struct zns *zns = ctrl->zns;
    ZNSParams *ssd_param = &zns->sp;
    uint64_t nchnls = ssd_param->nchnls;
    uint64_t chnls_per_zone = ssd_param->chnls_per_zone;
    uint64_t ways = ssd_param->ways;
    uint64_t ways_per_zone = ssd_param->ways_per_zone;
    uint64_t planes_per_die = ssd_param->planes_per_die;
    uint64_t zidx = zns_get_physical_zone_idx(ns, slba);
    uint64_t slpa_origin = (slba >> 3) / ZNS_PAGE_PARALLELISM;
    uint64_t slpa = slpa_origin / planes_per_die;

    // @inho : ppa(4K) distributed to 1. channels and 2. ways in interleaving manner (considering actual pagesize).   
    uint64_t zone_concurrency = (nchnls / chnls_per_zone) * (ways / ways_per_zone);
    uint64_t big_iter = zidx / zone_concurrency;
    uint64_t big_iter_val = zone_pages * zone_concurrency * planes_per_die;
    uint64_t med_iter = (zidx / (nchnls / chnls_per_zone)) % (ways / ways_per_zone);
    uint64_t med_iter_val = nchnls * ways_per_zone * planes_per_die;
    uint64_t small_iter = zidx % (nchnls / chnls_per_zone);
    uint64_t small_iter_val = (chnls_per_zone % nchnls) * planes_per_die;
    uint64_t start = big_iter * big_iter_val + med_iter * med_iter_val + small_iter * small_iter_val;

    uint64_t iter_chnl_way = (slpa / ssd_param->chnls_per_zone / ssd_param->ways_per_zone) % 
        (zone_pages / ssd_param->chnls_per_zone  / ssd_param->ways_per_zone);
    uint64_t iter_chnl_way_val = ssd_param->nchnls * ssd_param->ways *ssd_param->planes_per_die;
    uint64_t iter_chnl = (slpa / ssd_param->chnls_per_zone) % (ssd_param->ways_per_zone);
    uint64_t iter_chnl_val = ssd_param->nchnls * ssd_param->planes_per_die;
    uint64_t incre = (slpa % ssd_param->chnls_per_zone) * ssd_param->planes_per_die;
    uint64_t increp = slpa_origin % ssd_param->planes_per_die;

    return start + (iter_chnl_way * iter_chnl_way_val) + (iter_chnl * iter_chnl_val) + incre + increp;
}

// Get plane of the address
static inline uint64_t zns_get_plane_idx(NvmeNamespace *ns, uint64_t slba)
{
    FemuCtrl *n = ns->ctrl;
    struct zns *zns = n->zns;
    ZNSParams *ssd_param = &zns->sp;
    uint64_t ppn = zns_get_ppn_idx(ns, slba);
    return ppn % (ssd_param->nchnls * ssd_param->ways * ssd_param->dies_per_chip * ssd_param->planes_per_die);
}

// Get chip of the address
static inline uint64_t zns_get_chip_idx(NvmeNamespace *ns, uint64_t slba)
{
    FemuCtrl *n = ns->ctrl;
    struct zns *zns = n->zns;
    ZNSParams *ssd_param = &zns->sp;
    // Why is zidx not used here?
    // uint64_t zidx = zns_get_zone_idx(ns, slba);
    uint64_t ppn = zns_get_ppn_idx(ns,slba);
    return (ppn / ssd_param->planes_per_die) % (ssd_param->nchnls * ssd_param->ways);
}

/**
 * @brief Inhoinno, get plba, return chnl index considerring controller-level zone mapping (static zone mapping)
 *  
 * @param ns        namespace
 * @param slba      start lba
 * @return chnl_idx
 */
static inline uint64_t zns_get_chnl_idx(NvmeNamespace *ns, uint64_t slba)
{    
    FemuCtrl *n = ns->ctrl;
    struct zns * zns = n->zns;
    ZNSParams *ssd_param = &zns->sp;
    return zns_get_chip_idx(ns, slba) % ssd_param->nchnls;
}

static inline NvmeZone *zns_get_zone_by_slba(NvmeNamespace *ns, uint64_t slba)
{
    FemuCtrl *n = ns->ctrl;
    uint32_t zone_idx = zns_get_logical_zone_idx(ns, slba);
    assert(zone_idx < n->num_zones);
    return &n->zvtable->entries[zone_idx].logical_zone;
}

static inline NvmeZone *zns_get_physical_zone_by_slba(NvmeNamespace *ns, uint64_t slba)
{
    FemuCtrl *n = ns->ctrl;
    uint32_t zone_idx = zns_get_logical_zone_idx(ns, slba);
    assert(zone_idx < n->num_zones);
    return n->zvtable->entries[zone_idx].physical_zone;
}

static inline zns_vtable_entry* zns_get_vtable_entry_by_slba(NvmeNamespace *ns, uint64_t slba)
{
    FemuCtrl *n = ns->ctrl;
    uint32_t zone_idx = zns_get_logical_zone_idx(ns, slba);
    assert(zone_idx < n->num_zones);
    return &n->zvtable->entries[zone_idx];
}

static inline void zns_set_physical_zone(NvmeNamespace *ns, zns_vtable_entry *ventry, NvmeZone *zone) {
    ventry->physical_zone = zone;
    if (zone == NULL) {
        femu_err("Set zone logical %lu (%lu)-> NULL \n", 
            zns_get_logical_zone_idx(ns, ventry->logical_zone.d.zslba),
            ventry->logical_zone.d.zslba);
    } else {
        femu_err("Set zone logical %lu (%lu)-> physical %lu (%lu)\n", 
            zns_get_logical_zone_idx(ns, ventry->logical_zone.d.zslba),
            ventry->logical_zone.d.zslba,
            zns_get_logical_zone_idx(ns, ventry->physical_zone->d.zslba),
            ventry->physical_zone->d.zslba);
    }
}


static inline void zns_assign_physical_zone(FemuCtrl *n, zns_vtable_entry* ventry) {
    struct zns *zns = n->zns; 
    ZNSParams *spp = &zns->sp; 
    NvmeZone *physical_zone, *zone, *next;

    if (spp->vtable_mode == 1 && ventry->status == NVME_VZONE_UNASSIGNED) {
        // First check in free zones...
        if (!QTAILQ_EMPTY(&n->zvtable->free_zones)) {
            femu_err("Found free zone \n");
            physical_zone = QTAILQ_FIRST(&n->zvtable->free_zones);
            zns_set_physical_zone(&n->namespaces[0], ventry, physical_zone);
            ventry->physical_zone = physical_zone;   
            ventry->status = NVME_VZONE_ACTIVE;
            QTAILQ_REMOVE(&n->zvtable->free_zones, physical_zone, entry);
            QTAILQ_INSERT_TAIL(&n->zvtable->active_zones, physical_zone, entry);
        }
        // Then in used zones...
        else if (!QTAILQ_EMPTY(&n->zvtable->invalid_zones)) {
            femu_err("Found invalid zone \n");
            physical_zone = QTAILQ_LAST(&n->zvtable->invalid_zones);
            zns_set_physical_zone(&n->namespaces[0], ventry, physical_zone);
            ventry->physical_zone = physical_zone;   
            ventry->status = NVME_VZONE_INVALID;
            QTAILQ_REMOVE(&n->zvtable->invalid_zones, physical_zone, entry);
            QTAILQ_INSERT_TAIL(&n->zvtable->active_zones, physical_zone, entry);
        }
        // if neither error
        else {
            femu_err("Fatal error assigning physical to virtual zone\n");
            assert(false);
        }
    }
    assert(ventry->physical_zone && ventry->status != NVME_VZONE_UNASSIGNED);
}

static int zns_init_zone_geometry(NvmeNamespace *ns, Error **errp)
{
    FemuCtrl *n = ns->ctrl;
    uint64_t zone_size, zone_cap;
    uint32_t lbasz = 1 << zns_ns_lbads(ns);
    if (n->zone_size_bs) {
        zone_size = n->zone_size_bs;
    } else {
        zone_size = ZNS_ZONE_SIZE_BYTES;
    }

    if (n->zone_cap_bs) {
        zone_cap = n->zone_cap_bs;
    } else {
        zone_cap = zone_size;
    }

    femu_err("Zone size %lu zone cap %lu\n", zone_size, zone_cap);

    if (zone_cap > zone_size) {
        femu_err("zone capacity %luB > zone size %luB", zone_cap, zone_size);
        return -1;
    }
    if (zone_size < lbasz) {
        femu_err("zone size %luB too small, must >= %uB", zone_size, lbasz);
        return -1;
    }
    if (zone_cap < lbasz) {
        femu_err("zone capacity %luB too small, must >= %uB", zone_cap, lbasz);
        return -1;
    }

    femu_err("ZNS zone size %lu\n", n->zone_size);

    n->zone_size = zone_size / lbasz;
    n->zone_capacity = zone_cap / lbasz;
    n->num_zones = ns->size / lbasz / n->zone_size;

    if (n->max_open_zones > n->num_zones) {
        femu_err("max_open_zones value %u exceeds the number of zones %u",
                 n->max_open_zones, n->num_zones);
        return -1;
    }
    if (n->max_active_zones > n->num_zones) {
        femu_err("max_active_zones value %u exceeds the number of zones %u",
                 n->max_active_zones, n->num_zones);
        return -1;
    }

    if (n->zd_extension_size) {
        if (n->zd_extension_size & 0x3f) {
            femu_err("zone descriptor extension size must be multiples of 64B");
            return -1;
        }
        if ((n->zd_extension_size >> 6) > 0xff) {
            femu_err("zone descriptor extension size is too large");
            return -1;
        }
    }
    return 0;
}

static inline void set_zone_start(NvmeZone* zone, FemuCtrl *n, uint64_t start) {
    zone->d.zt = NVME_ZONE_TYPE_SEQ_WRITE;

#if MK_ZONE_CONVENTIONAL
    if( (i & (UINT32_MAX << MK_ZONE_CONVENTIONAL)) == 0){
        zone->d.zt = NVME_ZONE_TYPE_CONVENTIONAL;}
#endif
    zns_set_zone_state(zone, NVME_ZONE_STATE_EMPTY);
    zone->d.za = 0;
    zone->d.zcap = n->zone_capacity;
    zone->d.zslba = start;
    zone->d.wp = start;
    zone->w_ptr = start;
}

static void zns_init_zoned_state(NvmeNamespace *ns)
{
    FemuCtrl *n = ns->ctrl;
    uint64_t start = 0, zone_size = n->zone_size;
    uint64_t capacity = n->num_zones * zone_size;
    NvmeZone *zone;
    struct zns_vtable_entry *ventry;
    uint32_t i;
    n->zone_array = g_new0(NvmeZone, n->num_zones);
    
    // Vtable
    n->zvtable = g_malloc0(sizeof(struct zns_vtable));
    n->zvtable->entries = g_new0(zns_vtable_entry, n->num_zones);
    n->zvtable->number_of_zones = n->num_zones;
    QTAILQ_INIT(&n->zvtable->free_zones);
    QTAILQ_INIT(&n->zvtable->invalid_zones);
    QTAILQ_INIT(&n->zvtable->active_zones);

    if (n->zd_extension_size) {
        n->zd_extensions = g_malloc0(n->zd_extension_size * n->num_zones);
    }

    QTAILQ_INIT(&n->exp_open_zones);
    QTAILQ_INIT(&n->imp_open_zones);
    QTAILQ_INIT(&n->closed_zones);
    QTAILQ_INIT(&n->full_zones);

    zone = n->zone_array;
    ventry = n->zvtable->entries;
    for (i = 0; i < n->num_zones; i++, zone++, ventry++) {
        // All zone are active and will remain active
        QTAILQ_INSERT_TAIL(&n->zvtable->active_zones, zone, entry);

        if (start + zone_size > capacity) {
            zone_size = capacity - start;
        }

        set_zone_start(zone, n, start);
        set_zone_start(&(ventry->logical_zone), n, start);

        start += zone_size;
    }

    n->zone_size_log2 = 0;
    if (is_power_of_2(n->zone_size)) {
        n->zone_size_log2 = 63 - clz64(n->zone_size);   // 11= 63 - 52 
        femu_err("zone_size_log2 : %u (64MB : 2^26, 512B = 2^9)\n",n->zone_size_log2);
    }
}

static void  zns_init_zone_identify(FemuCtrl *n, NvmeNamespace *ns, int lba_index)
{
    NvmeIdNsZoned *id_ns_z;
    zns_init_zoned_state(ns);

    id_ns_z = g_malloc0(sizeof(NvmeIdNsZoned));

    /* MAR/MOR are zeroes-based, 0xffffffff means no limit */
    id_ns_z->mar = cpu_to_le32(n->max_active_zones - 1);
    id_ns_z->mor = cpu_to_le32(n->max_open_zones - 1);
    id_ns_z->zoc = 0;
    id_ns_z->ozcs = n->cross_zone_read ? 0x01 : 0x00;

    id_ns_z->lbafe[lba_index].zsze = cpu_to_le64(n->zone_size);
    id_ns_z->lbafe[lba_index].zdes = n->zd_extension_size >> 6; /* Units of 64B */

    n->csi = NVME_CSI_ZONED;
    ns->id_ns.nsze = cpu_to_le64(n->num_zones * n->zone_size);
    ns->id_ns.ncap = ns->id_ns.nsze;
    ns->id_ns.nuse = ns->id_ns.ncap;

    /* NvmeIdNs */
    /*
     * The device uses the BDRV_BLOCK_ZERO flag to determine the "deallocated"
     * status of logical blocks. Since the spec defines that logical blocks
     * SHALL be deallocated when then zone is in the Empty or Offline states,
     * we can only support DULBE if the zone size is a multiple of the
     * calculated NPDG.
     */
    if (n->zone_size % (ns->id_ns.npdg + 1)) {
        femu_err("the zone size (%"PRIu64" blocks) is not a multiple of the"
                 "calculated deallocation granularity (%"PRIu16" blocks); DULBE"
                 "support disabled", n->zone_size, ns->id_ns.npdg + 1);
        ns->id_ns.nsfeat &= ~0x4;
    }

    n->id_ns_zoned = id_ns_z;
}

// TODO: @KD add vzone compatibility
static void zns_clear_zone(NvmeNamespace *ns, NvmeZone *zone)
{
    FemuCtrl *n = ns->ctrl;
    uint8_t state;
    zone->w_ptr = zone->d.wp;
    state = zns_get_zone_state(zone);
    if (zone->d.wp != zone->d.zslba ||
        (zone->d.za & NVME_ZA_ZD_EXT_VALID)) {
        if (state != NVME_ZONE_STATE_CLOSED) {
            zns_set_zone_state(zone, NVME_ZONE_STATE_CLOSED);
        }
        zns_aor_inc_active(ns);
        QTAILQ_INSERT_HEAD(&n->closed_zones, zone, entry);
    } else {
        zns_set_zone_state(zone, NVME_ZONE_STATE_EMPTY);
    }
}

static void zns_zoned_ns_shutdown(NvmeNamespace *ns)
{
    FemuCtrl *n = ns->ctrl;
    NvmeZone *zone, *next;

    QTAILQ_FOREACH_SAFE(zone, &n->closed_zones, entry, next) {
        QTAILQ_REMOVE(&n->closed_zones, zone, entry);
        zns_aor_dec_active(ns);
        zns_clear_zone(ns, zone);
    }
    QTAILQ_FOREACH_SAFE(zone, &n->imp_open_zones, entry, next) {
        QTAILQ_REMOVE(&n->imp_open_zones, zone, entry);
        zns_aor_dec_open(ns);
        zns_aor_dec_active(ns);
        zns_clear_zone(ns, zone);
    }
    QTAILQ_FOREACH_SAFE(zone, &n->exp_open_zones, entry, next) {
        QTAILQ_REMOVE(&n->exp_open_zones, zone, entry);
        zns_aor_dec_open(ns);
        zns_aor_dec_active(ns);
        zns_clear_zone(ns, zone);
    }

    assert(n->nr_open_zones == 0);
}

void zns_ns_shutdown(NvmeNamespace *ns)
{
    FemuCtrl *n = ns->ctrl;

    if (n->zoned) {
        zns_zoned_ns_shutdown(ns);
    }
}

void zns_ns_cleanup(NvmeNamespace *ns)
{
    FemuCtrl *n = ns->ctrl;

    if (n->zoned) {
        g_free(n->id_ns_zoned);
        g_free(n->zone_array);
        g_free(n->zd_extensions);

        g_free(n->zvtable->entries);
        g_free(n->zvtable);
    }
}

static void zns_assign_zone_state(NvmeNamespace *ns, NvmeZone *zone,
                                  NvmeZoneState state)
{
    FemuCtrl *n = ns->ctrl;

    if (QTAILQ_IN_USE(zone, entry)) {
        switch (zns_get_zone_state(zone)) {
        case NVME_ZONE_STATE_EXPLICITLY_OPEN:
            QTAILQ_REMOVE(&n->exp_open_zones, zone, entry);
            break;
        case NVME_ZONE_STATE_IMPLICITLY_OPEN:
            QTAILQ_REMOVE(&n->imp_open_zones, zone, entry);
            break;
        case NVME_ZONE_STATE_CLOSED:
            QTAILQ_REMOVE(&n->closed_zones, zone, entry);
            break;
        case NVME_ZONE_STATE_FULL:
            QTAILQ_REMOVE(&n->full_zones, zone, entry);
        default:
            ;
        }
    }

    zns_set_zone_state(zone, state);

    switch (state) {
    case NVME_ZONE_STATE_EXPLICITLY_OPEN:
        QTAILQ_INSERT_TAIL(&n->exp_open_zones, zone, entry);
        break;
    case NVME_ZONE_STATE_IMPLICITLY_OPEN:
        QTAILQ_INSERT_TAIL(&n->imp_open_zones, zone, entry);
        break;
    case NVME_ZONE_STATE_CLOSED:
        QTAILQ_INSERT_TAIL(&n->closed_zones, zone, entry);
        break;
    case NVME_ZONE_STATE_FULL:
        QTAILQ_INSERT_TAIL(&n->full_zones, zone, entry);
    case NVME_ZONE_STATE_READ_ONLY:
        break;
    default:
        zone->d.za = 0;
    }
}

/*
 * Check if we can open a zone without exceeding open/active limits.
 * AOR stands for "Active and Open Resources" (see TP 4053 section 2.5).
 */
static int zns_aor_check(NvmeNamespace *ns, uint32_t act, uint32_t opn)
{
    FemuCtrl *n = ns->ctrl;

    if (n->max_active_zones != 0 &&
        n->nr_active_zones + act > n->max_active_zones) {
        return NVME_ZONE_TOO_MANY_ACTIVE | NVME_DNR;
    }
    if (n->max_open_zones != 0 &&
        n->nr_open_zones + opn > n->max_open_zones) {
        return NVME_ZONE_TOO_MANY_OPEN | NVME_DNR;
    }

    return NVME_SUCCESS;
}

static uint16_t zns_check_zone_state_for_write(NvmeZone *zone)
{
    uint16_t status;

    switch (zns_get_zone_state(zone)) {
    case NVME_ZONE_STATE_EMPTY:
    case NVME_ZONE_STATE_IMPLICITLY_OPEN:
    case NVME_ZONE_STATE_EXPLICITLY_OPEN:
    case NVME_ZONE_STATE_CLOSED:
        status = NVME_SUCCESS;
        break;
    case NVME_ZONE_STATE_FULL:
        status = NVME_ZONE_FULL;
        break;
    case NVME_ZONE_STATE_OFFLINE:
        status = NVME_ZONE_OFFLINE;
        break;
    case NVME_ZONE_STATE_READ_ONLY:
        status = NVME_ZONE_READ_ONLY;
        break;
    default:
        assert(false);
    }

    return status;
}

static uint16_t zns_check_zone_write(FemuCtrl *n, NvmeNamespace *ns,
                                      NvmeZone *zone, uint64_t slba,
                                      uint32_t nlb, bool append)
{
    uint16_t status;
    uint32_t zidx = zns_get_logical_zone_idx(ns, slba);
    if (unlikely((slba + nlb) > zns_zone_wr_boundary(zone))) {
        status = NVME_ZONE_BOUNDARY_ERROR;
    } else {
        status = zns_check_zone_state_for_write(zone);
    }

    if (status != NVME_SUCCESS) {
    } else {
        assert(zns_wp_is_valid(zone));
        if (append) {
            if (unlikely(slba != zone->d.zslba)) {
                //Zone Start Logical Block Address
                status = NVME_INVALID_FIELD;
            }
            if (zns_l2b(ns, nlb) > (n->page_size << n->zasl)) {
                status = NVME_INVALID_FIELD;
            }
            if((zidx < MK_ZONE_CONVENTIONAL)){
                femu_err("[inho] zns.c:406 append wp error(%d) in zidx=%d",status, zidx);
            }
        } else if (unlikely(slba != zone->w_ptr)) {
            
            status = NVME_ZONE_INVALID_WRITE;   
#if MK_ZONE_CONVENTIONAL
            if( (zidx < ( 1 << MK_ZONE_CONVENTIONAL)) ){
                //zidx & (UINT32_MAX << 3) == 0 //2^3 convs
                //NVME_ZONE_TYPE_CONVENTIONAL;
                zone->w_ptr = slba;
                //zone->w_ptr = zone->d.zslba;
                status = NVME_SUCCESS;
            }
#endif
        }
    }
    return status;
}

static uint16_t zns_check_zone_state_for_read(NvmeZone *zone)
{
    uint16_t status;

    switch (zns_get_zone_state(zone)) {
    case NVME_ZONE_STATE_EMPTY:
    case NVME_ZONE_STATE_IMPLICITLY_OPEN:
    case NVME_ZONE_STATE_EXPLICITLY_OPEN:
    case NVME_ZONE_STATE_FULL:
    case NVME_ZONE_STATE_CLOSED:
    case NVME_ZONE_STATE_READ_ONLY:
        status = NVME_SUCCESS;
        break;
    case NVME_ZONE_STATE_OFFLINE:
        status = NVME_ZONE_OFFLINE;
        break;
    default:
        assert(false);
    }

    return status;
}

static uint16_t zns_check_zone_read(NvmeNamespace *ns, uint64_t slba,
                                    uint32_t nlb)
{
    FemuCtrl *n = ns->ctrl;
    NvmeZone *logical_zone = zns_get_zone_by_slba(ns, slba);
    uint64_t bndry = zns_zone_rd_boundary(ns, logical_zone);
    uint64_t end = slba + nlb;
    uint16_t status;

    status = zns_check_zone_state_for_read(logical_zone);
    if (status != NVME_SUCCESS) {
        ;
    } else if (unlikely(end > bndry)) {
        if (!n->cross_zone_read) {
            femu_err("zns_check_zone_read BOUNDARY ERROR end %lu bndry %lu \n", end, bndry);
            status = NVME_ZONE_BOUNDARY_ERROR;
        } else {
            /*
             * Read across zone boundary - check that all subsequent
             * zones that are being read have an appropriate state.
             */
            do {
                logical_zone++;
                status = zns_check_zone_state_for_read(logical_zone);
                if (status != NVME_SUCCESS) {
                    break;
                }
            } while (end > zns_zone_rd_boundary(ns, logical_zone));
        }
    }

    return status;
}

static void zns_auto_transition_zone(NvmeNamespace *ns)
{
    FemuCtrl *n = ns->ctrl;
    NvmeZone *zone;

    if (n->max_open_zones &&
        n->nr_open_zones == n->max_open_zones) {
        zone = QTAILQ_FIRST(&n->imp_open_zones);
        if (zone) {
             /* Automatically close this implicitly open zone */
            QTAILQ_REMOVE(&n->imp_open_zones, zone, entry);
            zns_aor_dec_open(ns);
            // TODO: @kd add vzone support
            zns_assign_zone_state(ns, zone, NVME_ZONE_STATE_CLOSED);
        }
    }
}

// TODO: @kd add vzone support
static uint16_t zns_auto_open_zone(NvmeNamespace *ns, zns_vtable_entry* ventry)
{
    NvmeZone* logical_zone = &ventry->logical_zone;
    uint16_t status = NVME_SUCCESS;
    uint8_t zs = zns_get_zone_state(logical_zone);

    if (zs == NVME_ZONE_STATE_EMPTY) {
        zns_auto_transition_zone(ns);
        status = zns_aor_check(ns, 1, 1);
    } else if (zs == NVME_ZONE_STATE_CLOSED) {
        zns_auto_transition_zone(ns);
        status = zns_aor_check(ns, 0, 1);
    }

    return status;
}

static void zns_finalize_zoned_write(NvmeNamespace *ns, NvmeRequest *req,
                                     bool failed)
{
    NvmeRwCmd *rw = (NvmeRwCmd *)&req->cmd;
    zns_vtable_entry *ventry;
    NvmeZonedResult *res = (NvmeZonedResult *)&req->cqe;
    uint64_t slba;
    uint32_t nlb;

    slba = le64_to_cpu(rw->slba);
    nlb = le16_to_cpu(rw->nlb) + 1;
    ventry = zns_get_vtable_entry_by_slba(ns, slba);
    NvmeZone *logical_zone  = &ventry->logical_zone;
    NvmeZone *physical_zone = ventry->physical_zone;

    logical_zone->d.wp += nlb;
    physical_zone->d.wp += nlb;

    if (failed) {
        res->slba = 0;
    }

    if (logical_zone->d.wp == zns_zone_wr_boundary(logical_zone)) {
        switch (zns_get_zone_state(logical_zone)) {
        case NVME_ZONE_STATE_IMPLICITLY_OPEN:
        case NVME_ZONE_STATE_EXPLICITLY_OPEN:
            zns_aor_dec_open(ns);
            /* fall through */
        case NVME_ZONE_STATE_CLOSED:
            zns_aor_dec_active(ns);
            /* fall through */
        case NVME_ZONE_STATE_EMPTY:
            zns_assign_zone_state(ns, logical_zone, NVME_ZONE_STATE_FULL);
            zns_set_zone_state(physical_zone, NVME_ZONE_STATE_FULL);
            /* fall through */
        case NVME_ZONE_STATE_FULL:
            break;
        default:
            assert(false);
        }
    }
}

static uint64_t zns_advance_zone_wp(NvmeNamespace *ns, zns_vtable_entry *ventry,
                                    uint32_t nlb)
{
    NvmeZone* logical_zone  = &ventry->logical_zone; 
    NvmeZone* physical_zone = ventry->physical_zone; 

    uint64_t result = logical_zone->w_ptr;
    uint8_t zs;

    logical_zone->w_ptr += nlb;
    physical_zone->w_ptr += nlb;

    if (logical_zone->w_ptr < zns_zone_wr_boundary(logical_zone)) {
        zs = zns_get_zone_state(logical_zone);
        switch (zs) {
        case NVME_ZONE_STATE_EMPTY:
            zns_aor_inc_active(ns);
            /* fall through */
        case NVME_ZONE_STATE_CLOSED:
            zns_aor_inc_open(ns);
            zns_assign_zone_state(ns, logical_zone, NVME_ZONE_STATE_IMPLICITLY_OPEN);
            zns_set_zone_state(physical_zone, NVME_ZONE_STATE_IMPLICITLY_OPEN);
        }
    }

    return result;
}

// Note that we do NOT set vzones here, this can be done at a later point in time
static void zns_aio_zone_reset_cb(NvmeRequest *req, NvmeZone *zone)
{
    NvmeNamespace *ns = req->ns;

    /* FIXME, We always assume reset SUCCESS */
    switch (zns_get_zone_state(zone)) {
    case NVME_ZONE_STATE_EXPLICITLY_OPEN:
        /* fall through */
    case NVME_ZONE_STATE_IMPLICITLY_OPEN:
        zns_aor_dec_open(ns);
        /* fall through */
    case NVME_ZONE_STATE_CLOSED:
        zns_aor_dec_active(ns);
        /* fall through */
    case NVME_ZONE_STATE_FULL:
        zone->w_ptr = zone->d.zslba;
        zone->d.wp = zone->w_ptr;
        zns_assign_zone_state(ns, zone, NVME_ZONE_STATE_EMPTY);
    default:
        break;
    }
}

typedef uint16_t (*op_handler_t)(NvmeNamespace *, NvmeZone *, NvmeZoneState,
                                 NvmeRequest *);

enum NvmeZoneProcessingMask {
    NVME_PROC_CURRENT_ZONE    = 0,
    NVME_PROC_OPENED_ZONES    = 1 << 0,
    NVME_PROC_CLOSED_ZONES    = 1 << 1,
    NVME_PROC_READ_ONLY_ZONES = 1 << 2,
    NVME_PROC_FULL_ZONES      = 1 << 3,
};

// TODO: KD add assigning the physical_zone here
static uint16_t zns_open_zone(NvmeNamespace *ns, NvmeZone *zone,
                              NvmeZoneState state, NvmeRequest *req)
{
    uint16_t status;

    switch (state) {
    case NVME_ZONE_STATE_EMPTY:
        status = zns_aor_check(ns, 1, 0);
        if (status != NVME_SUCCESS) {
            return status;
        }
        zns_aor_inc_active(ns);
        /* fall through */
    case NVME_ZONE_STATE_CLOSED:
        status = zns_aor_check(ns, 0, 1);
        if (status != NVME_SUCCESS) {
            if (state == NVME_ZONE_STATE_EMPTY) {
                zns_aor_dec_active(ns);
            }
            return status;
        }
        zns_aor_inc_open(ns);
        /* fall through */
    case NVME_ZONE_STATE_IMPLICITLY_OPEN:
        zns_assign_zone_state(ns, zone, NVME_ZONE_STATE_EXPLICITLY_OPEN);
        /* fall through */
    case NVME_ZONE_STATE_EXPLICITLY_OPEN:
        return NVME_SUCCESS;
    default:
        return NVME_ZONE_INVAL_TRANSITION;
    }
}

static uint16_t zns_close_zone(NvmeNamespace *ns, NvmeZone *zone,
                               NvmeZoneState state, NvmeRequest *req)
{
    switch (state) {
    case NVME_ZONE_STATE_EXPLICITLY_OPEN:
        /* fall through */
    case NVME_ZONE_STATE_IMPLICITLY_OPEN:
        zns_aor_dec_open(ns);
        zns_assign_zone_state(ns, zone, NVME_ZONE_STATE_CLOSED);
        NvmeZone* physical_zone = zns_get_physical_zone_by_slba(ns, zone->d.zslba);
        zns_set_zone_state(physical_zone, NVME_ZONE_STATE_CLOSED);    
        /* fall through */
    case NVME_ZONE_STATE_CLOSED:
        return NVME_SUCCESS;
    default:
        return NVME_ZONE_INVAL_TRANSITION;
    }
}

// TODO: KD add finish functionality
static uint16_t zns_finish_zone(NvmeNamespace *ns, NvmeZone *zone,
                                NvmeZoneState state, NvmeRequest *req)
{
    switch (state) {
    case NVME_ZONE_STATE_EXPLICITLY_OPEN:
        /* fall through */
    case NVME_ZONE_STATE_IMPLICITLY_OPEN:
        zns_aor_dec_open(ns);
        /* fall through */
    case NVME_ZONE_STATE_CLOSED:
        zns_aor_dec_active(ns);
        /* fall through */
    case NVME_ZONE_STATE_EMPTY:
        zone->w_ptr = zns_zone_wr_boundary(zone);
        zone->d.wp = zone->w_ptr;
        zns_assign_zone_state(ns, zone, NVME_ZONE_STATE_FULL);
        /* fall through */
    case NVME_ZONE_STATE_FULL:
        return NVME_SUCCESS;
    default:
        return NVME_ZONE_INVAL_TRANSITION;
    }
}

static uint16_t zns_reset_zone(NvmeNamespace *ns, NvmeZone *zone,
                               NvmeZoneState state, NvmeRequest *req)
{
    switch (state) {
    case NVME_ZONE_STATE_EMPTY:
        return NVME_SUCCESS;
    case NVME_ZONE_STATE_EXPLICITLY_OPEN:
    case NVME_ZONE_STATE_IMPLICITLY_OPEN:
    case NVME_ZONE_STATE_CLOSED:
    case NVME_ZONE_STATE_FULL:
        break;
    default:
        return NVME_ZONE_INVAL_TRANSITION;
    }

    zns_aio_zone_reset_cb(req, zone);
    // TODO: KD add physical zone to reset to reset queue

    return NVME_SUCCESS;
}

static uint16_t zns_offline_zone(NvmeNamespace *ns, NvmeZone *zone,
                                 NvmeZoneState state, NvmeRequest *req)
{
    switch (state) {
    case NVME_ZONE_STATE_READ_ONLY:
        zns_assign_zone_state(ns, zone, NVME_ZONE_STATE_OFFLINE);
        NvmeZone* physical_zone = zns_get_physical_zone_by_slba(ns, zone->d.zslba);
        zns_set_zone_state(physical_zone, NVME_ZONE_STATE_OFFLINE);      
        /* fall through */
    case NVME_ZONE_STATE_OFFLINE:
        return NVME_SUCCESS;
    default:
        return NVME_ZONE_INVAL_TRANSITION;
    }
}

static uint16_t zns_set_zd_ext(NvmeNamespace *ns, NvmeZone *zone)
{
    uint16_t status;
    uint8_t state = zns_get_zone_state(zone);

    if (state == NVME_ZONE_STATE_EMPTY) {
        status = zns_aor_check(ns, 1, 0);
        if (status != NVME_SUCCESS) {
            return status;
        }
        zns_aor_inc_active(ns);
        zone->d.za |= NVME_ZA_ZD_EXT_VALID;
        zns_assign_zone_state(ns, zone, NVME_ZONE_STATE_CLOSED);
        return NVME_SUCCESS;
    }

    return NVME_ZONE_INVAL_TRANSITION;
}

static uint16_t zns_bulk_proc_zone(NvmeNamespace *ns, NvmeZone *zone,
                                   enum NvmeZoneProcessingMask proc_mask,
                                   op_handler_t op_hndlr, NvmeRequest *req)
{
    uint16_t status = NVME_SUCCESS;
    NvmeZoneState zs = zns_get_zone_state(zone);
    bool proc_zone;

    switch (zs) {
    case NVME_ZONE_STATE_IMPLICITLY_OPEN:
    case NVME_ZONE_STATE_EXPLICITLY_OPEN:
        proc_zone = proc_mask & NVME_PROC_OPENED_ZONES;
        break;
    case NVME_ZONE_STATE_CLOSED:
        proc_zone = proc_mask & NVME_PROC_CLOSED_ZONES;
        break;
    case NVME_ZONE_STATE_READ_ONLY:
        proc_zone = proc_mask & NVME_PROC_READ_ONLY_ZONES;
        break;
    case NVME_ZONE_STATE_FULL:
        proc_zone = proc_mask & NVME_PROC_FULL_ZONES;
        break;
    default:
        proc_zone = false;
    }

    if (proc_zone) {
        status = op_hndlr(ns, zone, zs, req);
    }

    return status;
}

static uint16_t zns_do_zone_op(NvmeNamespace *ns, NvmeZone *zone,
                               enum NvmeZoneProcessingMask proc_mask,
                               op_handler_t op_hndlr, NvmeRequest *req)
{
    FemuCtrl *n = ns->ctrl;
    NvmeZone *next;
    uint16_t status = NVME_SUCCESS;
    int i;

    if (!proc_mask) {
        status = op_hndlr(ns, zone, zns_get_zone_state(zone), req);
    } else {
        if (proc_mask & NVME_PROC_CLOSED_ZONES) {
            QTAILQ_FOREACH_SAFE(zone, &n->closed_zones, entry, next) {
                status = zns_bulk_proc_zone(ns, zone, proc_mask, op_hndlr,
                                             req);
                if (status && status != NVME_NO_COMPLETE) {
                    goto out;
                }
            }
        }
        if (proc_mask & NVME_PROC_OPENED_ZONES) {
            QTAILQ_FOREACH_SAFE(zone, &n->imp_open_zones, entry, next) {
                status = zns_bulk_proc_zone(ns, zone, proc_mask, op_hndlr,
                                             req);
                if (status && status != NVME_NO_COMPLETE) {
                    goto out;
                }
            }

            QTAILQ_FOREACH_SAFE(zone, &n->exp_open_zones, entry, next) {
                status = zns_bulk_proc_zone(ns, zone, proc_mask, op_hndlr,
                                             req);
                if (status && status != NVME_NO_COMPLETE) {
                    goto out;
                }
            }
        }
        if (proc_mask & NVME_PROC_FULL_ZONES) {
            QTAILQ_FOREACH_SAFE(zone, &n->full_zones, entry, next) {
                status = zns_bulk_proc_zone(ns, zone, proc_mask, op_hndlr,
                                             req);
                if (status && status != NVME_NO_COMPLETE) {
                    goto out;
                }
            }
        }

        if (proc_mask & NVME_PROC_READ_ONLY_ZONES) {
            for (i = 0; i < n->num_zones; i++, zone++) {
                status = zns_bulk_proc_zone(ns, zone, proc_mask, op_hndlr,
                                             req);
                if (status && status != NVME_NO_COMPLETE) {
                    goto out;
                }
            }
        }
    }

out:
    return status;
}

static uint16_t zns_get_mgmt_zone_slba_idx(FemuCtrl *n, NvmeCmd *c,
                                           uint64_t *slba, uint32_t *logical_zone_idx, uint32_t *physical_zone_idx)
{
    NvmeNamespace *ns = &n->namespaces[0];
    uint32_t dw10 = le32_to_cpu(c->cdw10);
    uint32_t dw11 = le32_to_cpu(c->cdw11);

    if (!n->zoned) {
        return NVME_INVALID_OPCODE | NVME_DNR;
    }

    *slba = ((uint64_t)dw11) << 32 | dw10;
    if (unlikely(*slba >= ns->id_ns.nsze)) {
        *slba = 0;
        return NVME_LBA_RANGE | NVME_DNR;
    }

    *logical_zone_idx = zns_get_logical_zone_idx(ns, *slba);
    assert(*logical_zone_idx < n->num_zones);
    *physical_zone_idx = zns_get_physical_zone_idx(ns, *slba);
    assert(*physical_zone_idx < n->num_zones);

    return NVME_SUCCESS;
}

// TODO: KD transition to vzone here
static uint16_t zns_zone_mgmt_send(FemuCtrl *n, NvmeRequest *req)
{
    struct zns *zns = n->zns;
    ZNSParams *spp = &zns->sp; 
    NvmeCmd *cmd = (NvmeCmd *)&req->cmd;
    NvmeNamespace *ns = req->ns;
    uint64_t prp1 = le64_to_cpu(cmd->dptr.prp1);
    uint64_t prp2 = le64_to_cpu(cmd->dptr.prp2);
    NvmeZone *logical_zone, *physical_zone;
    uintptr_t *resets;
    uint8_t *zd_ext;
    uint32_t dw13 = le32_to_cpu(cmd->cdw13);
    uint64_t slba = 0;
    uint32_t logical_zone_idx = 0;
    uint32_t physical_zone_idx = 0;
    uint16_t status;
    uint8_t action;
    bool all;
    enum NvmeZoneProcessingMask proc_mask = NVME_PROC_CURRENT_ZONE;
    zns_vtable_entry* ventry;

    action = dw13 & 0xff;
    all = dw13 & 0x100;

    req->status = NVME_SUCCESS;
    //req->stime
    if (!all) {
        status = zns_get_mgmt_zone_slba_idx(n, cmd, &slba, &logical_zone_idx, &physical_zone_idx);
        if (status) {
            return status;
        }
    }

    // zone = &n->zone_array[logical_zone_idx];
    logical_zone = &n->zvtable->entries[logical_zone_idx].logical_zone;
    physical_zone = n->zvtable->entries[logical_zone_idx].physical_zone;
    if (slba != logical_zone->d.zslba) {
        return NVME_INVALID_FIELD | NVME_DNR;
    }

    switch (action) {
    case NVME_ZONE_ACTION_OPEN:
        if (all) {
            proc_mask = NVME_PROC_CLOSED_ZONES;
        }
        status = zns_do_zone_op(ns, logical_zone, proc_mask, zns_open_zone, req);
        zns_set_zone_state(physical_zone, logical_zone->d.zs);
        break;
    case NVME_ZONE_ACTION_CLOSE:
        if (all) {
            proc_mask = NVME_PROC_OPENED_ZONES;
        }
        status = zns_do_zone_op(ns, logical_zone, proc_mask, zns_close_zone, req);
        zns_set_zone_state(physical_zone, logical_zone->d.zs);
        break;
    case NVME_ZONE_ACTION_FINISH:
        if (all) {
            proc_mask = NVME_PROC_OPENED_ZONES | NVME_PROC_CLOSED_ZONES;
        }
        req->expire_time += zns_advance_status(n, ns, cmd, req);
        // femu_err("Finishing a zone at %u  %lu %lu / %lu\n", logical_zone_idx, zone->w_ptr, 
        //     zone->d.zslba, zns_zone_wr_boundary(zone));
        if (logical_zone->w_ptr + FINISH_BLOCK_SIZE >= zns_zone_wr_boundary(logical_zone) || 
            logical_zone->w_ptr == logical_zone->d.zslba) {
            femu_err("Done finished\n");
            status = zns_do_zone_op(ns, logical_zone, proc_mask, zns_finish_zone, req);
            zns_set_zone_state(physical_zone, logical_zone->d.zs);
            cmd->cdw13 =  cpu_to_le32(le32_to_cpu(cmd->cdw13) | 0x100);
                    femu_err("Done finished?\n");
        } else {
            logical_zone->w_ptr += FINISH_BLOCK_SIZE;
            physical_zone->w_ptr += FINISH_BLOCK_SIZE;
            femu_err("zone->wptr %lu %lu %lu\n", logical_zone->w_ptr, physical_zone->w_ptr, FINISH_BLOCK_SIZE);
        }
        // femu_err("zone finish action:%c slba:%ld zone_idx:%d req->expire_time(%lu) - req->stime(%lu):%lu\n",
        //    action, req->slba ,logical_zone_idx,req->expire_time,req->stime,(req->expire_time - req->stime));
        // femu_err("Finished a zone at %lu\n", req->slba);
        break;
    case NVME_ZONE_ACTION_RESET:
        resets = (uintptr_t *)&req->opaque;

        if (all) {
            proc_mask = NVME_PROC_OPENED_ZONES | NVME_PROC_CLOSED_ZONES |
                NVME_PROC_FULL_ZONES;
        }
        *resets = 1;

        n->zvtable->entries[logical_zone_idx].logical_zone.cnt_reset += 1;
        if (spp->vtable_mode == 0) {
            req->expire_time += zns_advance_status(n, ns, cmd, req);
            status = zns_do_zone_op(ns, logical_zone, proc_mask, zns_reset_zone, req);
            zns_set_zone_state(physical_zone, logical_zone->d.zs);
            logical_zone->w_ptr = physical_zone->w_ptr = physical_zone->d.zslba;
            // femu_err("Reset %lu to %lu\n", logical_zone_idx, logical_zone->w_ptr);
            n->zvtable->entries[logical_zone_idx].physical_zone->cnt_reset += 1;
        } else {
            femu_err("Erasing zone %lu\n", logical_zone_idx);
            status = zns_do_zone_op(ns, logical_zone, proc_mask, zns_reset_zone, req);
            ventry = zns_get_vtable_entry_by_slba(ns, slba);
            // Mark as unused
            if (physical_zone) {
                if (QTAILQ_IN_USE(physical_zone, entry)) {
                    QTAILQ_REMOVE(&n->zvtable->active_zones, physical_zone, entry);
                }
                QTAILQ_INSERT_HEAD(&n->zvtable->invalid_zones, physical_zone, entry);
                zns_set_physical_zone(&n->namespaces[0], ventry, NULL);
                ventry->status = NVME_VZONE_UNASSIGNED;
            }
        }

        (*resets)--;
        // femu_err("zone reset    action:%c   slba:%ld     zone_idx:%d    req->expire_time(%lu) - req->stime(%lu):%lu\n",action, req->slba ,zone_idx,req->expire_time,req->stime,(req->expire_time - req->stime));
        return NVME_SUCCESS;
    case NVME_ZONE_ACTION_OFFLINE:
        if (all) {
            proc_mask = NVME_PROC_READ_ONLY_ZONES;
        }
        status = zns_do_zone_op(ns, logical_zone, proc_mask, zns_offline_zone, req);
        zns_set_zone_state(physical_zone, logical_zone->d.zs);
        break;
    case NVME_ZONE_ACTION_SET_ZD_EXT:
        if (all || !n->zd_extension_size) {
            return NVME_INVALID_FIELD | NVME_DNR;
        }
        zd_ext = zns_get_zd_extension(ns, logical_zone_idx);
        status = dma_write_prp(n, (uint8_t *)zd_ext, n->zd_extension_size, prp1,
                               prp2);
        if (status) {
            return status;
        }
        status = zns_set_zd_ext(ns, logical_zone);
        if (status == NVME_SUCCESS) {
            return status;
        }
        break;
    default:
        status = NVME_INVALID_FIELD;
    }

    if (status) {
        status |= NVME_DNR;
    }

    return status;
}

static bool zns_zone_matches_filter(uint32_t zafs, NvmeZone *zl)
{
    NvmeZoneState zs = zns_get_zone_state(zl);

    switch (zafs) {
    case NVME_ZONE_REPORT_ALL:
        return true;
    case NVME_ZONE_REPORT_EMPTY:
        return zs == NVME_ZONE_STATE_EMPTY;
    case NVME_ZONE_REPORT_IMPLICITLY_OPEN:
        return zs == NVME_ZONE_STATE_IMPLICITLY_OPEN;
    case NVME_ZONE_REPORT_EXPLICITLY_OPEN:
        return zs == NVME_ZONE_STATE_EXPLICITLY_OPEN;
    case NVME_ZONE_REPORT_CLOSED:
        return zs == NVME_ZONE_STATE_CLOSED;
    case NVME_ZONE_REPORT_FULL:
        return zs == NVME_ZONE_STATE_FULL;
    case NVME_ZONE_REPORT_READ_ONLY:
        return zs == NVME_ZONE_STATE_READ_ONLY;
    case NVME_ZONE_REPORT_OFFLINE:
        return zs == NVME_ZONE_STATE_OFFLINE;
    default:
        return false;
    }
}

static uint16_t zns_zone_mgmt_recv(FemuCtrl *n, NvmeRequest *req)
{
    NvmeCmd *cmd = (NvmeCmd *)&req->cmd;
    NvmeNamespace *ns = req->ns;
    uint64_t prp1 = le64_to_cpu(cmd->dptr.prp1);
    uint64_t prp2 = le64_to_cpu(cmd->dptr.prp2);
    /* cdw12 is zero-based number of dwords to return. Convert to bytes */
    uint32_t data_size = (le32_to_cpu(cmd->cdw12) + 1) << 2;
    uint32_t dw13 = le32_to_cpu(cmd->cdw13);
    uint32_t logical_zone_idx, physical_zone_idx, zra, zrasf, partial;
    uint64_t max_zones, nr_zones = 0;
    uint16_t status;
    uint64_t slba, capacity = zns_ns_nlbas(ns);
    NvmeZoneDescr *z;
    NvmeZone *zone;
    NvmeZoneReportHeader *header;
    void *buf, *buf_p;
    size_t zone_entry_sz;

    req->status = NVME_SUCCESS;

    status = zns_get_mgmt_zone_slba_idx(n, cmd, &slba, &logical_zone_idx, &physical_zone_idx);
    if (status) {
        return status;
    }

    zra = dw13 & 0xff;
    if (zra != NVME_ZONE_REPORT && zra != NVME_ZONE_REPORT_EXTENDED) {
        return NVME_INVALID_FIELD | NVME_DNR;
    }
    if (zra == NVME_ZONE_REPORT_EXTENDED && !n->zd_extension_size) {
        return NVME_INVALID_FIELD | NVME_DNR;
    }

    zrasf = (dw13 >> 8) & 0xff;
    if (zrasf > NVME_ZONE_REPORT_OFFLINE) {
        return NVME_INVALID_FIELD | NVME_DNR;
    }

    if (data_size < sizeof(NvmeZoneReportHeader)) {
        return NVME_INVALID_FIELD | NVME_DNR;
    }

    status = nvme_check_mdts(n, data_size);
    if (status) {
        return status;
    }

    partial = (dw13 >> 16) & 0x01;

    zone_entry_sz = sizeof(NvmeZoneDescr);
    if (zra == NVME_ZONE_REPORT_EXTENDED) {
        zone_entry_sz += n->zd_extension_size;
    }

    max_zones = (data_size - sizeof(NvmeZoneReportHeader)) / zone_entry_sz;
    buf = g_malloc0(data_size);

    zone = &n->zvtable->entries[logical_zone_idx].logical_zone;
    for (; slba < capacity; slba += n->zone_size) {
        if (partial && nr_zones >= max_zones) {
            break;
        }
        if (zns_zone_matches_filter(zrasf, zone++)) {
            nr_zones++;
        }
    }
    header = (NvmeZoneReportHeader *)buf;
    header->nr_zones = cpu_to_le64(nr_zones);

    buf_p = buf + sizeof(NvmeZoneReportHeader);
    for (; logical_zone_idx < n->num_zones && max_zones > 0; logical_zone_idx++) {
        zone = &n->zvtable->entries[logical_zone_idx].logical_zone;
        if (zns_zone_matches_filter(zrasf, zone)) {
            z = (NvmeZoneDescr *)buf_p;
            buf_p += sizeof(NvmeZoneDescr);

            z->zt = zone->d.zt;
            z->zs = zone->d.zs;
            z->zcap = cpu_to_le64(zone->d.zcap);
            z->zslba = cpu_to_le64(zone->d.zslba);
            z->za = zone->d.za;

            if (zns_wp_is_valid(zone)) {
                z->wp = cpu_to_le64(zone->d.wp);
            } else {
                z->wp = cpu_to_le64(~0ULL);
            }

            if (zra == NVME_ZONE_REPORT_EXTENDED) {
                if (zone->d.za & NVME_ZA_ZD_EXT_VALID) {
                    memcpy(buf_p, zns_get_zd_extension(ns, logical_zone_idx),
                           n->zd_extension_size);
                }
                buf_p += n->zd_extension_size;
            }

            max_zones--;
        }
    }

    status = dma_read_prp(n, (uint8_t *)buf, data_size, prp1, prp2);

    g_free(buf);

    return status;
}

static inline bool nvme_csi_has_nvm_support(NvmeNamespace *ns)
{
    switch (ns->ctrl->csi) {
    case NVME_CSI_NVM:
    case NVME_CSI_ZONED:
        return true;
    }
    return false;
}

static inline uint16_t zns_check_bounds(NvmeNamespace *ns, uint64_t slba,
                                        uint32_t nlb)
{
    uint64_t nsze = le64_to_cpu(ns->id_ns.nsze);

    if (unlikely(UINT64_MAX - slba < nlb || slba + nlb > nsze)) {
        return NVME_LBA_RANGE | NVME_DNR;
    }

    return NVME_SUCCESS;
}

static uint16_t zns_map_dptr(FemuCtrl *n, size_t len, NvmeRequest *req)
{
    uint64_t prp1, prp2;

    switch (req->cmd.psdt) {
    case NVME_PSDT_PRP:
        prp1 = le64_to_cpu(req->cmd.dptr.prp1);
        prp2 = le64_to_cpu(req->cmd.dptr.prp2);

        return nvme_map_prp(&req->qsg, &req->iov, prp1, prp2, len, n);
    default:
        return NVME_INVALID_FIELD;
    }
}

static uint64_t zns_advance_status_reset_physical(NvmeRequest *req, ZNS *zns, NvmeZone *physical_zone) {
    NvmeNamespace *ns = req->ns;
    FemuCtrl *n = ns->ctrl;
    ZNSParams * spp = &zns->sp;
    zns_ssd_plane *plane = NULL;

    uint64_t slba = physical_zone->d.zslba;
    uint64_t cmd_stime = (req->stime == 0) ? qemu_clock_get_ns(QEMU_CLOCK_REALTIME) : req->stime;

    uint64_t maxlat = 0;
    uint64_t lat = 0;

    // Part of zone filled
    uint64_t blocks_to_erase = 0;
    {
        uint64_t filled = physical_zone->w_ptr - physical_zone->d.zslba;
        if (!filled) {
            return maxlat;
        }
        uint64_t zone_chunk = n->zone_capacity / spp->blocks_per_die;
        blocks_to_erase = spp->allow_partial_zone_resets ? (filled + zone_chunk - 1) / zone_chunk : spp->blocks_per_die;
    }

    // Erase blocks in chunks
    for (uint64_t b = 0; b < blocks_to_erase; b++) {
        // Get all associated planes
        for (int i = 0; i < spp->ways_per_zone * spp->chnls_per_zone; i++) {
            int step = i * (ZNS_INTERNAL_PAGE_SIZE / 512);
            uint64_t my_plane_idx = zns_get_plane_idx(ns, slba + step);
            // femu_err("DEBUG erasure: %lu %lu %lu %lu %lu %u\n", slba+step, zns_get_ppn_idx(ns, slba+step), my_plane_idx, 
            //     (spp->ways * spp->planes_per_die* spp->dies_per_chip * spp->nchnls), b, spp->allow_partial_zone_resets);
            plane= &(zns->planes[my_plane_idx]);
            plane->next_avail_time = plane->next_avail_time > cmd_stime ? 
                    plane->next_avail_time + spp->blk_er_lat : cmd_stime + spp->blk_er_lat;
            lat = plane->next_avail_time - cmd_stime;
            maxlat = (maxlat < lat) ? lat : maxlat;
            femu_err("Erasure %lu %lu %lu --- %lu out of %lu\n", my_plane_idx, lat, maxlat, spp->blk_er_lat, blocks_to_erase);
        }
    }
    return maxlat;
}


static uint16_t zns_do_append(FemuCtrl *n, NvmeRequest *req, bool append,
                             bool wrz)
{
    struct zns *zns = n->zns;
    NvmeRwCmd *rw = (NvmeRwCmd *)&req->cmd;
    NvmeNamespace *ns = req->ns;
    uint64_t slba = le64_to_cpu(rw->slba);
    uint32_t nlb = (uint32_t)le16_to_cpu(rw->nlb) + 1;
    uint64_t data_size = zns_l2b(ns, nlb);
    uint64_t data_offset;
    NvmeZone *logical_zone;
    zns_vtable_entry *ventry;
    NvmeZonedResult *res = (NvmeZonedResult *)&req->cqe;
    uint16_t status;
    uint64_t reqtime = 0, tmpreqtime = 0;

    assert(n->zoned);
    req->is_write = true;

    ventry = zns_get_vtable_entry_by_slba(ns, slba);
    logical_zone = &ventry->logical_zone;
    // Assign new zone?
    zns_assign_physical_zone(n, ventry);

    if (!wrz) {
        status = nvme_check_mdts(n, data_size);
        if (status) {
            goto err;
        }
    }

    status = zns_check_bounds(ns, slba, nlb);
    if (status) {
        goto err;
    }

    //pthread_spin_lock(&zone->w_ptr_lock);
    status = zns_check_zone_write(n, ns, logical_zone, slba, nlb, append);

    if (status) {
        goto err;
    }

    status = zns_auto_open_zone(ns, ventry);
    if (status) {
        goto err;
    }

    // Erase invalidated zone..
    ZNSParams *spp = &zns->sp; 
    if (spp->vtable_mode == 1 && ventry->status == NVME_VZONE_INVALID) {
        reqtime = zns_advance_status_reset_physical(req, zns, ventry->physical_zone);
        ventry->status = NVME_VZONE_ACTIVE;
    }

    if (append) {
        slba = logical_zone->w_ptr;
    }
    data_offset = zns_l2b(ns, slba);

    if (!wrz) {
        status = zns_map_dptr(n, data_size, req);
        if (status) {
            goto err;
        }
        
        tmpreqtime = zns_advance_status(n,ns,(NvmeCmd *)&req->cmd,req);
        reqtime = tmpreqtime > reqtime ? tmpreqtime : reqtime;
        req->expire_time += reqtime;
        backend_rw(n->mbe, &req->qsg, &data_offset, req->is_write);
    }
    res->slba = zns_advance_zone_wp(ns, ventry, nlb);
    zns_finalize_zoned_write(ns, req, false);
    //pthread_spin_unlock(&zone->w_ptr_lock);

    return NVME_SUCCESS;

err:
    printf("****************Append Failed***************\n");
    return status | NVME_DNR;
}

static uint16_t zns_admin_cmd(FemuCtrl *n, NvmeCmd *cmd)
{

    switch (cmd->opcode) {
        
    default:
        femu_err("zns_admin_cmd fallout cmd->opcode %x %d", cmd->opcode, cmd->opcode);
        return NVME_INVALID_OPCODE | NVME_DNR;
    }
}

static inline uint16_t zns_zone_append(FemuCtrl *n, NvmeRequest *req)
{
    return zns_do_append(n, req, true, false);
}

static uint16_t zns_check_dulbe(NvmeNamespace *ns, uint64_t slba, uint32_t nlb)
{
    return NVME_SUCCESS;
}

static uint64_t zns_advance_status_write(ZNS *zns, NvmeRequest *req){
    //FEMU only supports 1 namespace for now (see femu.c:365)
    //and FEMU ZNS Extension use a single thread which mean lockless operations(ch->available_time += ~~) if thread increased
    NvmeRwCmd *rw = (NvmeRwCmd *)&req->cmd;
    struct NvmeNamespace *ns = req->ns;
    ZNSParams * spp = &zns->sp; 
    uint64_t slba = le64_to_cpu(rw->slba);
    uint32_t nlb = (uint32_t)le16_to_cpu(rw->nlb) + 1;
    uint64_t currlat = 0, maxlat = 0;
    zns_ssd_channel *chnl = NULL;
    zns_ssd_plane *plane = NULL;

    chnl = &(zns->ch[0]);
    pthread_spin_lock(&(chnl->time_lock));


    // To get accurate append latency we need to change the slba to the zone pointer (we do not send all requests to slba even for appends).
        NvmeZone *zone;
    {
        zone = zns_get_zone_by_slba(ns, slba);
        slba = zone->w_ptr;
    }

    uint64_t nand_stime = 0;
    uint64_t cmd_stime = 0;

    uint32_t my_plane_idx = 0;
    uint32_t my_chnl_idx = 0;
    uint64_t chnl_stime = req->stime == 0 ? qemu_clock_get_ns(QEMU_CLOCK_REALTIME) : req->stime;


    if (req->stime == 0) {
        cmd_stime = qemu_clock_get_ns(QEMU_CLOCK_REALTIME);
    } else {
        cmd_stime = req->stime;
    }

    uint64_t step_size = (ZNS_INTERNAL_PAGE_SIZE / 512);
    for (uint64_t i = 0; i < nlb ; i += step_size) {
        my_chnl_idx=zns_get_chnl_idx(ns, slba); 
        my_plane_idx = zns_get_plane_idx(ns, slba); 

        chnl = &(zns->ch[my_chnl_idx]);
        plane= &(zns->planes[my_plane_idx]);

        //pthread_spin_lock(&(chnl->time_lock));
        chnl_stime = (chnl->next_ch_avail_time < cmd_stime) ? \
            cmd_stime : chnl->next_ch_avail_time;
        chnl->next_ch_avail_time = chnl_stime + spp->ch_xfer_lat;
        //pthread_spin_unlock(&(chnl->time_lock));

        // if (zone->w_ptr - zone->d.zslba < 64*4) {
        //     femu_err("TESTINGA %lu %lu %lu  -- time %lu %li (idle %lu)", slba, my_chnl_idx, my_plane_idx, 
        //         chnl_stime - cmd_stime, (plane->next_avail_time < cmd_stime) ? 0  : \
        //         plane->next_avail_time - cmd_stime, 
        //         (plane->next_avail_time < cmd_stime) ? cmd_stime - plane->next_avail_time  : \
        //         0);
        // }

        nand_stime = (plane->next_avail_time < chnl->next_ch_avail_time) ? chnl->next_ch_avail_time : \
            plane->next_avail_time;
        plane->next_avail_time = nand_stime + spp->pg_wr_lat;
        
        currlat = plane->next_avail_time - cmd_stime;
        maxlat = (maxlat < currlat) ? currlat : maxlat;
        
        // if (zone->w_ptr - zone->d.zslba < 64*4) {
        //     femu_err(" %lu %lu TESTINGB %lu %lu \n?", currlat, maxlat, chnl->next_ch_avail_time - cmd_stime,
        //          plane->next_avail_time -cmd_stime);
        // }
        
        slba += step_size;
    }

    chnl = &(zns->ch[0]);
    pthread_spin_unlock(&(chnl->time_lock));

    if (zone->w_ptr - zone->d.zslba < 1024) {
        // femu_err("Write lat %lu %lu\n", zone->w_ptr, maxlat);
    }

    // femu_err("Write lat %lu %lu\n", slba, maxlat);
    return maxlat;

}

static uint64_t zns_advance_status_read(ZNS *zns, NvmeRequest *req){
    // FEMU only supports 1 namespace for now (see femu.c:365) 
    // and FEMU ZNS Extension use a single thread which mean lockless operations(ch->available_time += ~~) if thread increased 

    NvmeRwCmd *rw = (NvmeRwCmd *)&req->cmd;
    uint64_t slba = le64_to_cpu(rw->slba);
    uint32_t nlb = (uint32_t)le16_to_cpu(rw->nlb) + 1;
    struct NvmeNamespace *ns = req->ns;
    ZNSParams * spp = &zns->sp; 
    //zns_ssd_lun *chip = NULL;
    zns_ssd_plane *plane = NULL;
    uint64_t currlat = 0, maxlat= 0;
    //uint32_t my_chip_idx = 0;
    uint32_t my_plane_idx = 0;
    uint64_t nand_stime =0;
    uint64_t cmd_stime = (req->stime == 0) ? qemu_clock_get_ns(QEMU_CLOCK_REALTIME) : req->stime ;
    zns_ssd_channel *chnl =NULL;
    uint32_t my_chnl_idx = 0;
    uint64_t chnl_stime =0;

    //uint64_t zidx= zns_get_zone_idx(ns, slba);
    //uint64_t slpa = (slba >> 3) / (ZNS_INTERNAL_PAGE_SIZE/ZNS_EXTERNAL_PAGE_SIZE);
    // 8:4K 32:16K 64:32K 128:64K
    uint64_t step_size = (ZNS_INTERNAL_PAGE_SIZE / 512);
    for (uint64_t i = 0; i < nlb; i += step_size) {
        my_chnl_idx = zns_get_chnl_idx(ns, slba); 
        my_plane_idx = zns_get_plane_idx(ns, slba);
        chnl = &(zns->ch[my_chnl_idx]);
        plane= &(zns->planes[my_plane_idx]);

        //Inhoinno:  Single thread emulation so assume we dont need lock per chnl
        nand_stime = (plane->next_avail_time < cmd_stime) ? cmd_stime : \
                     plane->next_avail_time;
        plane->next_avail_time = nand_stime + spp->pg_rd_lat;

        chnl_stime = (chnl->next_ch_avail_time < plane->next_avail_time) ? \
            plane->next_avail_time : chnl->next_ch_avail_time;
        chnl->next_ch_avail_time = chnl_stime + spp->ch_xfer_lat;

        currlat = chnl->next_ch_avail_time - cmd_stime;
        maxlat = (maxlat < currlat)? currlat : maxlat;
        slba += step_size;
    }

    return maxlat;
}

/**
 * @brief 
 * 
 * @param n 
 * @param ns 
 * @param cmd 
 * @param req 
}*/
static uint64_t zns_advance_status_reset(ZNS *zns, NvmeRequest *req){
    NvmeCmd *cmd = (NvmeCmd *)&req->cmd;
    NvmeNamespace *ns = req->ns;
    FemuCtrl *n = ns->ctrl;
    uint32_t logical_zone_idx = 0;
    uint32_t physical_zone_idx = 0;
    uint64_t slba = 0;

    zns_get_mgmt_zone_slba_idx(n, cmd, &slba, &logical_zone_idx, &physical_zone_idx);

    return zns_advance_status_reset_physical(req, zns, n->zvtable->entries[logical_zone_idx].physical_zone);
}

static uint64_t zns_advance_status_finish(ZNS *zns, NvmeRequest *req){
    // For now just synchronous at high write size (note that we do not actually have to write something)
    NvmeCmd *cmd = (NvmeCmd *)&req->cmd;
    NvmeNamespace *ns = req->ns;
    FemuCtrl *n = ns->ctrl;
    ZNSParams * spp = &zns->sp;
    uint32_t logical_zone_idx = 0;
    uint32_t physical_zone_idx = 0;
    zns_ssd_channel *chnl = NULL;
    zns_ssd_plane *plane = NULL;
    uint32_t my_plane_idx = 0;
    uint32_t my_chnl_idx = 0;

    uint64_t slba = 0;
    uint64_t cmd_stime = (req->stime == 0) ? qemu_clock_get_ns(QEMU_CLOCK_REALTIME) : req->stime;

    uint64_t maxlat = 0;
    uint64_t lat = 0;
    uint64_t nand_stime = 0;
    uint64_t chnl_stime = 0;

    finishing = 1;
    finishing = 0;

    // Get pages to write
    zns_get_mgmt_zone_slba_idx(n, cmd, &slba, &logical_zone_idx, &physical_zone_idx);
    NvmeZone *logical_zone  = &n->zvtable->entries[logical_zone_idx].logical_zone;
    uint64_t pages_to_write = n->zone_capacity - (logical_zone->w_ptr - logical_zone->d.zslba);

    pages_to_write = pages_to_write > FINISH_BLOCK_SIZE ? FINISH_BLOCK_SIZE : pages_to_write;

    // Nothing to write, but there is some RTT latency account for that
    if (!pages_to_write || pages_to_write == n->zone_capacity) {
        slba = logical_zone->w_ptr;
        my_chnl_idx=zns_get_chnl_idx(ns, slba); 
        chnl = &(zns->ch[my_chnl_idx]);
        chnl_stime = (chnl->next_ch_avail_time < cmd_stime) ? cmd_stime : chnl->next_ch_avail_time;
        chnl->next_ch_avail_time = chnl_stime + spp->ch_xfer_lat;
        lat = chnl->next_ch_avail_time - cmd_stime;
        maxlat = (maxlat < lat) ? lat : maxlat;

        return maxlat;
    }

    // Direct blocking

    // Chunk based
    slba = logical_zone->w_ptr;
    uint64_t step_size = (ZNS_INTERNAL_PAGE_SIZE / 512);
    for (uint64_t i = 0; i < pages_to_write ; i += step_size) {
        my_chnl_idx=zns_get_chnl_idx(ns, slba); 
        my_plane_idx = zns_get_plane_idx(ns, slba); 
        chnl = &(zns->ch[my_chnl_idx]);
        plane= &(zns->planes[my_plane_idx]);

        chnl_stime = (chnl->next_ch_avail_time < cmd_stime) ? \
            cmd_stime : chnl->next_ch_avail_time;
        chnl->next_ch_avail_time = chnl_stime + spp->ch_xfer_lat;

        nand_stime = (plane->next_avail_time < chnl->next_ch_avail_time) ? chnl->next_ch_avail_time : \
            plane->next_avail_time;
        plane->next_avail_time = nand_stime + spp->pg_wr_lat;

        lat = plane->next_avail_time - cmd_stime;
        maxlat = (maxlat < lat) ? lat : maxlat;
        slba += step_size;
    }

    return maxlat;
}

static uint64_t zns_advance_status(FemuCtrl *n, NvmeNamespace *ns, NvmeCmd *cmd, NvmeRequest *req){
    
    NvmeRwCmd *rw = (NvmeRwCmd *)&req->cmd;
    uint8_t opcode = rw->opcode;
    uint32_t dw13 = le32_to_cpu(cmd->cdw13);

    uint8_t action;
    action = dw13 & 0xff;
    uint64_t out = 0;

    // Zone Reset 
    if (action == NVME_ZONE_ACTION_RESET){
        //reset zone->wp and zone->status=Empty
        //reset zone, causing every chip lat +
        out = zns_advance_status_reset(n->zns, req);
        return out;
    }
    // Finish
    if (action == NVME_ZONE_ACTION_FINISH) {
        out = zns_advance_status_finish(n->zns, req);
        return out;
    }
    // Read, Write 
    assert(opcode == NVME_CMD_WRITE || opcode == NVME_CMD_READ || opcode == NVME_CMD_ZONE_APPEND);
    if(req->is_write) {
        out = zns_advance_status_write(n->zns, req);
    }
    else { 
        // femu_err("Going to read %u\n", finishing);
        out = zns_advance_status_read(n->zns, req);
        // femu_err("Read %u\n", finishing);
    }
    return out;
}

static uint16_t zns_io_read(FemuCtrl *n, NvmeNamespace *ns, NvmeCmd *cmd,
                         NvmeRequest *req)
{
    NvmeRwCmd *rw = (NvmeRwCmd *)&req->cmd;
    uint64_t slba = le64_to_cpu(rw->slba);
    uint32_t nlb = (uint32_t)le16_to_cpu(rw->nlb) + 1;
    uint64_t data_size = zns_l2b(ns, nlb);
    uint64_t data_offset;
    uint16_t status;
    zns_vtable_entry* ventry;
// #if PCIe_TIME_SIMULATION
//     uint64_t nk = nlb/2;
//     uint64_t delta_time = (uint64_t)nk*pow(10,9);   //n KB > 4096*1KB*2^10:10^9ns = 1KB : (10^9 / 2^10 / 4096)ns
//     //femu_err("[Inho ] delt : %lx            ",delta_time);
//     delta_time = delta_time/pow(2,10)/(Interface_PCIeGen3x4_bw);
//     PCIe_Gen3_x4 * pcie = n->pci_simulation;
// #endif
    assert(n->zoned);
    req->is_write = false;

    ventry = zns_get_vtable_entry_by_slba(ns, slba);

    status = nvme_check_mdts(n, data_size);
    if (status) {
        femu_err("nvme_check_mdts status %d %x\n",status,status);
        goto err;
    }

    status = zns_check_bounds(ns, slba, nlb);
    if (status) {
        femu_err("zns_check_bounds status d:%d x:%x slba:%lu nlb:%u\n",status,status,slba,nlb);
        goto err;
    }

    status = zns_check_zone_read(ns, slba, nlb);
    if (status) {
        femu_err("zns_check_zone_read status %d %x\n",status,status);
        goto err;
    }

    status = zns_map_dptr(n, data_size, req);
    if (status) {
        femu_err("zns_map_dptr status %d %x\n",status,status);
        goto err;
    }

    if (NVME_ERR_REC_DULBE(n->features.err_rec)) {
        femu_err("n->features.err_rec %d %x\n",status,status);
        status = zns_check_dulbe(ns, slba, nlb);
        if (status) {
            femu_err("zns_check_dulbe %d %x\n",status,status);
            goto err;
        }
    }
    // femu_err("read success?? slba %lu %d\n",slba, ventry->status);
    data_offset = zns_l2b(ns, slba);
    // For now treat read to an inactive zone as a noop
    if (ventry->status == NVME_VZONE_ACTIVE) {
        req->expire_time += zns_advance_status(n,ns,cmd,req);
    }
    /*PCI latency model here*/

//         lag=0;
//         pcie->stime = req->stime;
//         pcie->ntime = pcie->stime + Interface_PCIeGen3x4_bwmb/ZNS_ZASL_SIZE_BYTES/1000 * delta_time;
//         req->expire_time += 968*(req->nlb/8);
//     } else if(pcie->ntime < (pcie->stime + delta_time)){
//         //update lag
//         lag = (pcie->ntime - req->stime);
//         pcie->stime = pcie->ntime;
//         pcie->ntime = pcie->stime + Interface_PCIeGen3x4_bwmb/ZNS_ZASL_SIZE_BYTES/1000 * delta_time; //1ms
//         req->expire_time += lag;
//         pcie->stime += delta_time;
//     } else if (req->stime < pcie->ntime && lag != 0 ){
//         req->expire_time+=lag;
//     }
//     pcie->stime += delta_time;
//     //femu_err("[inho] lag : %lx\n", lag);
//     //pthread_spin_unlock(&n->pci_lock);
// #endif
    //unlock
    backend_rw(n->mbe, &req->qsg, &data_offset, req->is_write);
    return NVME_SUCCESS;

err:
    return status | NVME_DNR;
}


static uint16_t zns_io_write(FemuCtrl *n, NvmeNamespace *ns, NvmeCmd *cmd,
                          NvmeRequest *req)
{
    struct zns *zns = n->zns;
    NvmeRwCmd *rw = (NvmeRwCmd *)cmd;
    uint64_t slba = le64_to_cpu(rw->slba);
    uint32_t nlb = (uint32_t)le16_to_cpu(rw->nlb) + 1;
    uint64_t data_size = zns_l2b(ns, nlb);
    uint64_t data_offset;
    zns_vtable_entry* ventry;
    NvmeZone *logical_zone;
    NvmeZonedResult *res = (NvmeZonedResult *)&req->cqe;
    uint16_t status;
    uint64_t zidx = zns_get_logical_zone_idx(ns, slba);
    uint64_t err_zidx = 0;
    uint64_t reqtime = 0, tmpreqtime = 0;

    assert(n->zoned);
    req->is_write = true;
    //femu_err("PROFILING zns_write %lu\n", (req->expire_time -req->stime));

    ventry = zns_get_vtable_entry_by_slba(ns, slba);
    logical_zone = &ventry->logical_zone;
    // Assign new zone?
    zns_assign_physical_zone(n, ventry);

    status = nvme_check_mdts(n, data_size);
    if (status) {
        goto err;
    }

    status = zns_check_bounds(ns, slba, nlb);
    if (status) {
        femu_err("zns check bounds [pid %x] slba : %lx , nlb : %x\n", getpid(), slba, nlb);
        goto err;
    }

    //lock
    //pthread_spin_lock(&zone->w_ptr_lock);
    status = zns_check_zone_write(n, ns, logical_zone, slba, nlb, false);
    //unlock
    if (status) {
        err_zidx = zidx;
        femu_err("in zns_check_zone_write [pid %x] Zidx : %lx z.wtp : %lx , slba : %lx , nlb : %x\n", getpid() ,zidx, logical_zone->w_ptr, slba, nlb);
        goto err;
    }
    if(err_zidx > (1<<MK_ZONE_CONVENTIONAL)){
        femu_err("in errzidx:%lx [pid %x] Zidx : %lx z.wtp : %lx , slba : %lx, nlb : %x \n", err_zidx, getpid() ,zidx, logical_zone->w_ptr, slba, nlb);
    }
    status = zns_auto_open_zone(ns, ventry);
    if (status) {
        goto err;
    }
    // Erase invalidated zone..
    ZNSParams *spp = &zns->sp; 
    bool reset = false;
    if (spp->vtable_mode == 1 && ventry->status == NVME_VZONE_INVALID) {
        femu_err("Resetting physical zone first %lu\n", zidx);
        reqtime = zns_advance_status_reset_physical(req, zns, ventry->physical_zone);
        ventry->physical_zone->w_ptr = ventry->physical_zone->d.zslba;
        ventry->status = NVME_VZONE_ACTIVE;
        reset = true;
    }

    data_offset = zns_l2b(ns, slba);
    status = zns_map_dptr(n, data_size, req); // dptr:data pointer
    if (status) {
        goto err;
    }
    tmpreqtime = zns_advance_status(n,ns,cmd,req);
    if (reset) {
        femu_err("Resetting physical zone time %lu %lu %lu\n", reqtime, tmpreqtime, tmpreqtime > reqtime ? tmpreqtime : reqtime);
    }
    reqtime = tmpreqtime > reqtime ? tmpreqtime : reqtime;
    req->expire_time += reqtime;
    backend_rw(n->mbe, &req->qsg, &data_offset, req->is_write);
    //lock
    res->slba = zns_advance_zone_wp(ns, ventry, nlb);
    //unlock
    zns_finalize_zoned_write(ns, req, false);
    //pthread_spin_unlock(&zone->w_ptr_lock);

    return NVME_SUCCESS;

err:
    femu_err("*********ZONE WRITE FAILED*********, Zidx : %lx , STATUS : %x\n", zidx, status);  
    return status | NVME_DNR;
}

static uint16_t zns_io_cmd(FemuCtrl *n, NvmeNamespace *ns, NvmeCmd *cmd,
                           NvmeRequest *req)
{
    switch (cmd->opcode) {
    case NVME_CMD_READ:
        // femu_log("ZNS READ cmd->opcode %d %x\n",cmd->opcode, cmd->opcode);
        return zns_io_read(n, ns, cmd, req);
    case NVME_CMD_WRITE:
        // femu_log("ZNS WRITE cmd->opcode %d %x\n",cmd->opcode, cmd->opcode);
        return zns_io_write(n, ns, cmd, req);
    case NVME_CMD_ZONE_MGMT_SEND:
        return zns_zone_mgmt_send(n, req);
    case NVME_CMD_ZONE_MGMT_RECV:
        return zns_zone_mgmt_recv(n, req);
    case NVME_CMD_ZONE_APPEND:
        return zns_zone_append(n, req);
    }

    return NVME_INVALID_OPCODE | NVME_DNR;
}

static void zns_set_ctrl_str(FemuCtrl *n)
{
    static int fsid_zns = 0;
    const char *zns_mn = "FEMU ZNS-SSD Controller";
    const char *zns_sn = "vZNSSD";

    nvme_set_ctrl_name(n, zns_mn, zns_sn, &fsid_zns);
}

static void zns_set_ctrl(FemuCtrl *n)
{
    uint8_t *pci_conf = n->parent_obj.config;

    zns_set_ctrl_str(n);
    pci_config_set_vendor_id(pci_conf, PCI_VENDOR_ID_INTEL);
    pci_config_set_device_id(pci_conf, 0x5845);
}

static int zns_init_zone_cap(FemuCtrl *n)
{
    ZNSParams *spp = &(n->zns_params); 

    n->zoned = true;
    n->zasl_bs = spp->zasl;
    n->zone_size_bs = spp->zone_size;
    n->zone_cap_bs = spp->zone_cap_param;
    n->cross_zone_read = true;
    n->max_active_zones = 0;
    n->max_open_zones = 0;
    n->zd_extension_size = 0;

    return 0;
}

static int zns_start_ctrl(FemuCtrl *n)
{
    /* Coperd: let's fail early before anything crazy happens */
    assert(n->page_size == 4096);

    if (!n->zasl_bs) {
        n->zasl = n->mdts;
    } else {
        if (n->zasl_bs < n->page_size) {
            femu_err("ZASL too small (%dB), must >= 1 page (4K)\n", n->zasl_bs);
            return -1;
        }
        n->zasl = 31 - clz32(n->zasl_bs / n->page_size);
    }

    return 0;
}

static void zns_init(FemuCtrl *n, Error **errp)
{
    NvmeNamespace *ns = &n->namespaces[0];
    zns_set_ctrl(n);
    n->zns = g_malloc0(sizeof(struct zns));
    zns_init_zone_cap(n);
    if (zns_init_zone_geometry(ns, errp) != 0) {
        return;
    }

    zns_init_zone_identify(n, ns, 0);
    znsssd_init(n);
}

static void zns_init_vtable(FemuCtrl * n, ZNSParams *spp) {
    NvmeZone *zone = n->zone_array;
    uint64_t start = 0, zone_size = n->zone_size;  
    uint64_t capacity = n->num_zones * zone_size;
    struct zns_vtable_entry *ventry = n->zvtable->entries;
    uint32_t i;

    // Direct
    if (spp->vtable_mode == 0) {
        for (i = 0; i < n->num_zones; i++, zone++, ventry++) {
            // All zone are active and will remain active
            QTAILQ_INSERT_HEAD(&n->zvtable->active_zones, zone, entry);

            if (start + zone_size > capacity) {
                zone_size = capacity - start;
            }

            zns_set_physical_zone(&n->namespaces[0], ventry, zone);
            ventry->status = NVME_VZONE_ACTIVE;

            start += zone_size;
        }
    }
    // Lazy
    else {
        for (i = 0; i < n->num_zones; i++, zone++, ventry++) {
            // All physical zone start out as INACTIVE
            QTAILQ_INSERT_HEAD(&n->zvtable->free_zones, zone, entry);
            if (start + zone_size > capacity) {
                zone_size = capacity - start;
            }

            zns_set_physical_zone(&n->namespaces[0], ventry, NULL);
            ventry->status = NVME_VZONE_UNASSIGNED;

            start += zone_size;
        }
    }
}

static void znsssd_init_params(FemuCtrl * n, ZNSParams *spp){
    ZNSParams *spp_param = &(n->zns_params); 
    NvmeNamespace *ns = &n->namespaces[0];
    uint32_t lbasz = 1 << zns_ns_lbads(ns);

    spp->allow_partial_zone_resets = spp_param->allow_partial_zone_resets;
    spp->asynchronous_resets = spp_param->asynchronous_resets;
    spp->vtable_mode = spp_param->vtable_mode;

    spp->pg_rd_lat = spp_param->pg_rd_lat;
    spp->pg_wr_lat = spp_param->pg_wr_lat;
    spp->blk_er_lat = spp_param->blk_er_lat;
    spp->ch_xfer_lat = spp_param->ch_xfer_lat;
    // /**
    //  * 1. SSD size  2. zone size 3. # of chnls 4. # of chnls per zone
    // */
    spp->nchnls         = spp_param->nchnls;   //default : 8                                                   
    // /* FIXME : = ZNS_MAX_CHANNEL channel configuration like this */
    spp->chnls_per_zone = spp_param->chnls_per_zone ;   
    spp->zones          = n->num_zones;     
    spp->ways           = spp_param->ways;    //default : 2
    spp->ways_per_zone  = spp_param->ways_per_zone;    //default :==spp->ways
    spp->dies_per_chip  = spp_param->dies_per_chip;    //default : 1
    spp->planes_per_die = spp_param->planes_per_die;    //default : 4
    spp->block_size     = spp_param->block_size;
    uint64_t bytes_per_block = spp->block_size * ZNS_INTERNAL_PAGE_SIZE;
    uint64_t zns_stripe_size_bs = bytes_per_block * spp->ways_per_zone * spp->chnls_per_zone;
    femu_err("Stripe size %lu %lu %lu\n", n->zone_cap_bs, zns_stripe_size_bs, n->zone_cap_bs % zns_stripe_size_bs);
    assert((n->zone_capacity * lbasz) % zns_stripe_size_bs == 0);
    spp->blocks_per_die = (n->zone_capacity * lbasz)  / zns_stripe_size_bs;
    spp->register_model = spp_param->register_model;    
    /*Inho @ Temporarly, FEMU doesn't support more than 1 namespace. Parameters below is for supporting different zone configurations temporarly*/

    spp->chnls_per_another_zone = 7;
    /* TO REAL STORAGE SIZE */
    spp->csze_pages     = (((int64_t)n->memsz) * 1024 * 1024) / ZNS_EXTERNAL_PAGE_SIZE 
        / spp->nchnls / spp->ways;
    spp->nchips         = (((int64_t)n->memsz) * 1024 * 1024) 
        / ZNS_EXTERNAL_PAGE_SIZE / spp->csze_pages;
        
    femu_log("===========================================\n");
    femu_log("|        ConfZNS HW Configuration()       |\n");      
    femu_log("===========================================\n");
    femu_log("| proglat     : %lu   | readlat   : %lu   |\n", spp->pg_wr_lat, spp->pg_rd_lat);
    femu_log("| eraslat     : %lu   | xferlat   : %lu   |\n", spp->blk_er_lat, spp->ch_xfer_lat);
    femu_log("===========================================\n");
    femu_log("| nchnl       : %lu   | nway      : %lu   |\n", spp->nchnls, spp->ways);
    femu_log("| nchnl/zone  : %lu   | nway/zone : %lu   |\n", spp->chnls_per_zone, spp->ways_per_zone);
    femu_log("| die/chip    : %lu   | io_qs     : %u    |\n", spp->dies_per_chip, n->num_io_queues);
    femu_log("| plane/die   : %lu   | block/die : %lu  |\n", spp->planes_per_die, spp->blocks_per_die);
    femu_log("| pages/block : %lu   |  stripe   : %lu   |\n", spp->block_size, zns_stripe_size_bs / ZNS_INTERNAL_PAGE_SIZE);
    femu_log("| page        : %ldKiB|  zones    : %lu  |\n", (ZNS_INTERNAL_PAGE_SIZE/KiB), spp->zones);
    femu_log("===========================================\n");

    zns_init_vtable(n, spp);    
}

/**
 * @brief 
 * @Inhoinno: we need to make zns ssd latency emulation
 * in order to emulate controller-level mapping in ZNS
 * for example, 1-to-1 mapping or 1-to-All mapping (zone-channel) 
 * @param FemuCtrl for mapping channel for zones
 * @return none 
 */
static void zns_init_ch(struct zns_ssd_channel *ch, ZNSParams *spp)
{
    ch->next_ch_avail_time = 0;
    ch->busy = 0;
    int ret = pthread_spin_init(&(ch->time_lock), PTHREAD_PROCESS_SHARED);
    if(ret)
        femu_err("zns.c:1754 znssd_init(): lock alloc failed, to inhoinno \n");        
}

static void zns_init_chip(struct zns_ssd_lun *ch, ZNSParams *spp)
{
    ch->next_avail_time = 0;
    ch->busy = 0;
    
    int ret = pthread_spin_init(&(ch->time_lock), PTHREAD_PROCESS_SHARED);
    if(ret)
        femu_err("zns.c:1754 znssd_init(): lock alloc failed, to inhoinno \n");
}

static void zns_init_plane(struct zns_ssd_plane *pl, ZNSParams *spp)
{
    pl->next_avail_time=0;
    pl->busy=false;
    pl->nregs=spp->register_model;
}

void znsssd_init(FemuCtrl * n){
    struct zns *zns = n->zns;
    ZNSParams *spp = &zns->sp; 
    zns->namespaces = n->namespaces;
    znsssd_init_params(n, spp);
    uint64_t nplanes = (spp->ways * spp->planes_per_die* spp->dies_per_chip * spp->nchnls);
    
    femu_err("zns.c:1820 znssd_init(): nplanes %ld spp->ways %ld spp->planes_per_die %ld\
             spp->dies_per_chip %ld \
             spp->nchnls %ld \n ", nplanes, spp->ways, spp->planes_per_die, spp->dies_per_chip, spp->nchnls);
    /* initialize zns ssd internal layout architecture */
    zns->ch     = g_malloc0(sizeof(struct zns_ssd_channel) * spp->nchnls);
    zns->chips  = g_malloc0(sizeof(struct zns_ssd_lun) * spp->nchnls*spp->ways);
    zns->planes = g_malloc0(sizeof(struct zns_ssd_plane) * nplanes);
    zns->zone_array = n->zone_array;
    zns->num_zones = spp->zones;
    for(uint32_t i=0 ; i < n->num_zones; i++){
        int ret = pthread_spin_init(&(zns->zone_array[i].w_ptr_lock), PTHREAD_PROCESS_SHARED);
        n->zone_array[i].cnt_reset=0;
        if(ret)
            femu_err("zns.c:1687 znssd_init(): lock alloc failed, to inhoinno \n");
    }

    for (int i = 0; i < spp->nchnls; i++) {
        zns_init_ch(&zns->ch[i], spp);
    }
    for (int i = 0; i < spp->nchnls * spp->ways; i++) {
        zns_init_chip(&zns->chips[i], spp);
    }
    for (uint64_t i = 0; i < nplanes; i++){
        zns_init_plane(&zns->planes[i], spp);
    }
}

static void zns_exit(FemuCtrl *n)
{
    /*
     * Release any extra resource (zones) allocated for ZNS mode
     */
}

int nvme_register_znssd(FemuCtrl *n)
{
#ifdef INHOINNO_VERBOSE_SETTING
    femu_err("zns.c : nvme_register_znsssd(), to inhoinno \n");
#endif
    n->ext_ops = (FemuExtCtrlOps) {
        .state            = NULL,
        .init             = zns_init,
        .exit             = zns_exit,
        .rw_check_req     = NULL,
        .start_ctrl       = zns_start_ctrl,
        .admin_cmd        = zns_admin_cmd,
        .io_cmd           = zns_io_cmd,
        .get_log          = NULL,
    };

    return 0;
}
