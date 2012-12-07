"""Run through the Redis datastore looking at worker image keys. If any
of the workers haven't sent a pong update in so many seconds (300 by default),
then they are silently removed.
"""
import redis
import time

def poll_registered_workers():
    r = redis.StrictRedis()
    for key in r.keys('worker:*'):
        last_pong = float(r.hget(key, 'last_pong'))
        current_time = float('%.3f' % time.time())
        if abs(current_time - last_pong) >= 300:
            r.delete(key)
            print key, 'removed'
        else:
            print key, 'alive and well'

if __name__ == '__main__':
    poll_registered_workers()
