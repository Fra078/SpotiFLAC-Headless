import asyncio
import time
import unittest
from unittest.mock import Mock, AsyncMock

from SpotiFLAC.core.progress import DownloadManager, DownloadBroadcaster, DownloadStatus, ProgressCallback

class DownloadEventDrivenTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Reset the singleton state
        self.manager = DownloadManager()
        self.manager.reset()
        self.broadcaster = DownloadBroadcaster()
        
        # Clear broadcaster listeners
        with self.broadcaster._listener_lock:
            self.broadcaster._listeners.clear()
            self.broadcaster._loop = None
            self.broadcaster._last_broadcast_time = 0.0

    def tearDown(self):
        self.manager.reset()
        with self.broadcaster._listener_lock:
            self.broadcaster._listeners.clear()
            self.broadcaster._loop = None

    async def test_broadcaster_subscription(self):
        loop = asyncio.get_running_loop()
        q = asyncio.Queue()
        
        self.broadcaster.subscribe(q, loop)
        self.assertIn(q, self.broadcaster._listeners)
        self.assertEqual(self.broadcaster._loop, loop)
        
        # Broadcast something
        test_data = {"test": "data"}
        self.broadcaster.broadcast_immediate(test_data)
        
        # Wait a tiny bit for the threadsafe call to run
        await asyncio.sleep(0.05)
        
        self.assertFalse(q.empty())
        result = await q.get()
        self.assertEqual(result, test_data)
        
        self.broadcaster.unsubscribe(q)
        self.assertNotIn(q, self.broadcaster._listeners)

    async def test_download_manager_properties(self):
        # Initially not downloading and speed is 0
        self.assertFalse(self.manager.is_downloading)
        self.assertEqual(self.manager.current_speed, 0.0)

        # Add tracks
        self.manager.add_to_queue("track1", "Track 1", "Artist 1", "Album 1", "spotify1")
        self.manager.add_to_queue("track2", "Track 2", "Artist 2", "Album 2", "spotify2")

        # Start first
        self.manager.start_download("track1")
        self.assertTrue(self.manager.is_downloading)
        
        # Update progress and speed of first
        self.manager.update_progress("track1", 5.0, 10.0, 2.5) # item_id, progress, total, speed
        self.assertEqual(self.manager.current_speed, 2.5)
        
        # Start second (concurrent download)
        self.manager.start_download("track2")
        self.manager.update_progress("track2", 2.0, 8.0, 1.5)
        
        # Total speed should be sum of active speeds (2.5 + 1.5 = 4.0)
        self.assertEqual(self.manager.current_speed, 4.0)
        self.assertTrue(self.manager.is_downloading)

        # Complete first
        self.manager.complete_download("track1", "/path/to/file1.flac", 10.0)
        
        # is_downloading should still be True because track2 is still downloading
        self.assertTrue(self.manager.is_downloading)
        self.assertEqual(self.manager.current_speed, 1.5)

        # Complete second
        self.manager.complete_download("track2", "/path/to/file2.flac", 8.0)
        self.assertFalse(self.manager.is_downloading)
        self.assertEqual(self.manager.current_speed, 0.0)

    async def test_event_driven_broadcast_on_state_changes(self):
        loop = asyncio.get_running_loop()
        q = asyncio.Queue()
        self.broadcaster.subscribe(q, loop)

        # Add to queue should trigger broadcast
        self.manager.add_to_queue("track1", "Track 1", "Artist 1", "Album 1", "spotify1")
        await asyncio.sleep(0.05)
        self.assertFalse(q.empty())
        stats = await q.get()
        self.assertEqual(len(stats["queue"]), 1)
        self.assertEqual(stats["queue"][0]["status"], "queued")

        # Start download should trigger broadcast
        self.manager.start_download("track1")
        await asyncio.sleep(0.05)
        self.assertFalse(q.empty())
        stats = await q.get()
        self.assertEqual(stats["queue"][0]["status"], "downloading")

        # Complete download should trigger broadcast
        self.manager.complete_download("track1", "/path/to/file1.flac", 10.0)
        await asyncio.sleep(0.05)
        self.assertFalse(q.empty())
        stats = await q.get()
        self.assertEqual(stats["queue"][0]["status"], "completed")

    async def test_progress_broadcast_throttling(self):
        loop = asyncio.get_running_loop()
        q = asyncio.Queue()
        self.broadcaster.subscribe(q, loop)

        self.manager.add_to_queue("track1", "Track 1", "Artist 1", "Album 1", "spotify1")
        self.manager.start_download("track1")
        # Consume the startup events
        await asyncio.sleep(0.05)
        while not q.empty():
            await q.get()

        # Reset last broadcast time to simulate a long period since the startup event
        self.broadcaster._last_broadcast_time = 0.0

        # Update progress 1st time - should broadcast immediately (since last_broadcast_time is now 0)
        self.manager.update_progress("track1", 1.0, 10.0, 1.0)
        await asyncio.sleep(0.05)
        self.assertFalse(q.empty())
        await q.get()

        # Update progress 2nd time immediately - should NOT broadcast because of throttling (< 250ms)
        self.manager.update_progress("track1", 2.0, 10.0, 1.0)
        await asyncio.sleep(0.05)
        self.assertTrue(q.empty())

        # Wait for throttle window to pass (> 250ms)
        await asyncio.sleep(0.3)
        self.manager.update_progress("track1", 3.0, 10.0, 1.0)
        await asyncio.sleep(0.05)
        self.assertFalse(q.empty())
        await q.get()

    async def test_progress_callback(self):
        self.manager.add_to_queue("track1", "Track 1", "Artist 1", "Album 1", "spotify1")
        self.manager.start_download("track1")

        cb = ProgressCallback(item_id="track1", track_name="Track 1")
        # Simulate 1MB downloaded out of 10MB
        cb(1 * 1024 * 1024, 10 * 1024 * 1024)

        # Retrieve stats to verify progress and size are correctly recorded
        stats = self.manager.get_stats()
        track = stats["queue"][0]
        self.assertEqual(track["progress"], 1.0)
        self.assertEqual(track["total_size"], 10.0)


if __name__ == "__main__":
    unittest.main()
