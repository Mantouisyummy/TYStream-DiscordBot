import redis

import Constants



r = redis.Redis(host=Constants.REDIS_HOST, port=Constants.REDIS_PORT, password=Constants.REDIS_PASSWORD, db=0, decode_responses=True)

### === Twitch 相關緩存 === ###

def check_and_clear_twitch_streamer(streamer_id):
    """檢查 Twitch 實況主是否在線，若已下線則清除緩存"""
    if not is_twitch_streamer_live(streamer_id):
        clear_twitch_notified_streamer(streamer_id)

def check_and_clear_youtube_streamer(streamer_id):
    """檢查 YouTube 直播主是否在線，若已下線則清除緩存"""
    if not is_youtube_streamer_live(streamer_id):
        clear_youtube_notified_streamer(streamer_id)

def cache_twitch_guild_streamers(guild_id, streamers):
    """緩存特定 Guild 追蹤的 Twitch 實況主"""

    if not streamers:
        return

    r.sadd(f"twitch:guild_streamers:{guild_id}", *streamers)
    r.expire(f"twitch:guild_streamers:{guild_id}", 86400)


def remove_twitch_guild_streamers(guild_id, streamers) -> bool:
    """移除特定 Guild 追蹤的 Twitch 實況主"""
    if not streamers:
        return False

    if isinstance(streamers, str):
        streamers = [streamers]

    removed_count = r.srem(f"twitch:guild_streamers:{guild_id}", *streamers)
    return removed_count > 0 # 返回是否成功移除


def get_twitch_guild_streamers(guild_id):
    """獲取特定 Guild 追蹤的 Twitch 直播主"""
    return r.smembers(f"twitch:guild_streamers:{guild_id}")

def is_twitch_streamer_live(streamer_id):
    """檢查 Twitch 實況主是否在線"""
    return r.exists(f"twitch:live_streamer:{streamer_id}")

def cache_twitch_streamer_live(streamer_id, duration=60):
    r.setex(f"twitch:live_streamer:{streamer_id}", duration, "1")


def mark_twitch_as_notified(guild_id, streamer_id, message_id):
    """標記 Twitch 實況主已被通知"""
    key = f"twitch:notified_streams:{guild_id}"
    # 使用 hset 將訊息 ID 存儲在哈希中
    r.hset(key, streamer_id, message_id)
    return True

def get_twitch_message_id(guild_id, streamer_id):
    """獲取已通知的 Twitch 訊息 ID"""
    key = f"twitch:notified_streams:{guild_id}"
    return r.hget(key, streamer_id)


def has_twitch_notified(guild_id, streamer_id):
    """檢查 Twitch 實況主是否已被通知"""
    key = f"twitch:notified_streams:{guild_id}"
    return r.hexists(key, streamer_id)  # 檢查 Redis Hash 是否存在該主播的訊息 ID


def clear_twitch_notified_streamer(streamer_id):
    """清除 Twitch 已通知的直播狀態"""
    cursor = 0
    while True:
        cursor, keys = r.scan(cursor, match="twitch:notified_streams:*", count=100)
        for key in keys:
            # 使用 hdel 而不是 srem，因為我們在使用 hash 而不是 set
            if r.hexists(key, streamer_id):
                r.hdel(key, streamer_id)
        if cursor == 0:
            break

### === YouTube 相關緩存 === ###

def cache_youtube_guild_streamers(guild_id, streamers):
    """緩存特定 Guild 追蹤的 Youtube 實況主"""
    if not streamers:
        return
    r.sadd(f"youtube:guild_streamers:{guild_id}", *streamers)
    r.expire(f"youtube:guild_streamers:{guild_id}", 86400)

def remove_youtube_guild_streamers(guild_id, streamers):
    """移除特定 Guild 追蹤的 Twitch 實況主"""
    if not streamers:
        return

    if isinstance(streamers, str):
        streamers = [streamers]

    r.srem(f"youtube:guild_streamers:{guild_id}", *streamers)

def get_youtube_guild_streamers(guild_id):
    """獲取特定 Guild 追蹤的 YouTube 直播主"""
    return r.smembers(f"youtube:guild_streamers:{guild_id}")

def is_youtube_streamer_live(streamer_id):
    """檢查 YouTube 直播主是否在線"""
    return r.exists(f"youtube:live_streamer:{streamer_id}")

def cache_youtube_streamer_live(streamer_id, duration=10):
    """緩存 YouTube 直播狀態"""
    clear_youtube_notified_streamer(streamer_id)
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