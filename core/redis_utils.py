import redis

r = redis.Redis(host='100.99.177.51', port=5022, db=0, password="mantouisyummy")

def cache_guild_streamers(guild_id, streamers):
    """緩存所有Guild追蹤的實況主"""
    r.sadd(f"guild_streamers:{guild_id}", *streamers)
    r.expire(f"guild_streamers:{guild_id}", 86400)  # 24 小时过期

def clear_notified_streamer(streamer_id):
    keys = r.keys(f"notified_streams:*")
    for key in keys:
        r.srem(key, streamer_id)
    r.delete(f"live_streamer:{streamer_id}")

def get_guild_streamers(guild_id):
    """獲取特定Guild追蹤的直播主"""
    return r.smembers(f"guild_streamers:{guild_id}")

def has_notified(guild_id, streamer_id):
    """檢查是否已經通知過"""
    return r.sismember(f"notified_streams:{guild_id}", streamer_id)

def mark_as_notified(guild_id, streamer_id, duration=600):
    """標記已經通知過的直播"""
    r.sadd(f"notified_streams:{guild_id}", streamer_id)
    r.expire(f"notified_streams:{guild_id}", duration)

def is_streamer_live(streamer_id):
    """從Redis中查詢是否有緩存的直播狀態"""
    return r.exists(f"live_streamer:{streamer_id}")

def cache_streamer_live(streamer_id, duration=30):
    """緩存直播狀態"""
    r.setex(f"live_streamer:{streamer_id}", duration, "1")