from celery import shared_task

@shared_task
def warm_all_caches():
    """Warm up application caches"""
    print("Warming caches...")
 
    return "Caches warmed"

@shared_task
def invalidate_stale_caches():
    """Invalidate stale cache entries"""
    print("Invalidating stale caches...")
   
    return "Stale caches invalidated"