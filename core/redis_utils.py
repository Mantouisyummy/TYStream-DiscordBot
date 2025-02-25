import redis

import Constants

r = redis.Redis(host=Constants.REDIS_HOST, port=Constants.REDIS_PORT, password=Constants.REDIS_PASSWORD, db=0)

### === Twitch 相關緩存 === ###

def cache_twitch_guild_streamers(guild_id, streamers):
    """緩存特定 Guild 追蹤的 Twitch 實況主"""
    r.sadd(f"twitch:guild_streamers:{guild_id}", *streamers)
    r.expire(f"twitch:guild_streamers:{guild_id}", 86400)

def get_twitch_guild_streamers(guild_id):
    """獲取特定 Guild 追蹤的 Twitch 直播主"""
    return r.smembers(f"twitch:guild_streamers:{guild_id}")

def is_twitch_streamer_live(streamer_id):
    """檢查 Twitch 實況主是否在線"""
    return r.exists(f"twitch:live_streamer:{streamer_id}")

def cache_twitch_streamer_live(streamer_id, duration=30):
    """緩存 Twitch 直播狀態"""
    r.setex(f"twitch:live_streamer:{streamer_id}", duration, "1")

def mark_twitch_as_notified(guild_id, streamer_id, duration=600):
    """標記 Twitch 實況主已通知"""
    r.sadd(f"twitch:notified_streams:{guild_id}", streamer_id)
    r.expire(f"twitch:notified_streams:{guild_id}", duration)

def has_twitch_notified(guild_id, streamer_id):
    """檢查 Twitch 是否已通知"""
    return r.sismember(f"twitch:notified_streams:{guild_id}", streamer_id)

def clear_twitch_notified_streamer(streamer_id):
    """清除 Twitch 已通知的直播狀態"""
    keys = r.keys(f"twitch:notified_streams:*")
    for key in keys:
        r.srem(key, streamer_id)
    r.delete(f"twitch:live_streamer:{streamer_id}")


### === YouTube 相關緩存 === ###

def cache_youtube_guild_streamers(guild_id, streamers):
    """緩存特定 Guild 追蹤的 YouTube 直播主"""
    r.sadd(f"youtube:guild_streamers:{guild_id}", *streamers)
    r.expire(f"youtube:guild_streamers:{guild_id}", 86400)

def get_youtube_guild_streamers(guild_id):
    """獲取特定 Guild 追蹤的 YouTube 直播主"""
    return r.smembers(f"youtube:guild_streamers:{guild_id}")

def is_youtube_streamer_live(streamer_id):
    """檢查 YouTube 直播主是否在線"""
    return r.exists(f"youtube:live_streamer:{streamer_id}")

def cache_youtube_streamer_live(streamer_id, duration=30):
    """緩存 YouTube 直播狀態"""
    r.setex(f"youtube:live_streamer:{streamer_id}", duration, "1")

def mark_youtube_as_notified(guild_id, streamer_id, duration=600):
    """標記 YouTube 直播主已通知"""
    r.sadd(f"youtube:notified_streams:{guild_id}", streamer_id)
    r.expire(f"youtube:notified_streams:{guild_id}", duration)

def has_youtube_notified(guild_id, streamer_id):
    """檢查 YouTube 是否已通知"""
    return r.sismember(f"youtube:notified_streams:{guild_id}", streamer_id)

def clear_youtube_notified_streamer(streamer_id):
    """清除 YouTube 已通知的直播狀態"""
    keys = r.keys(f"youtube:notified_streams:*")
    for key in keys:
        r.srem(key, streamer_id)
    r.delete(f"youtube:live_streamer:{streamer_id}")