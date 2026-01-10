/**
 * Queue Manager - IndexedDB-based upload queue with retry logic
 *
 * Handles:
 * - Queueing failed voice uploads
 * - Auto-retry with exponential backoff
 * - Persistent storage across sessions
 * - Manual retry triggers
 */

const QUEUE_DB_NAME = 'CringeProofQueue';
const QUEUE_STORE_NAME = 'upload_queue';
const MAX_RETRY_ATTEMPTS = 5;
const INITIAL_RETRY_DELAY = 1000; // 1 second

class QueueManager {
  constructor() {
    this.db = null;
    this.isProcessing = false;
    this.initDB();
  }

  async initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(QUEUE_DB_NAME, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        console.log('[QueueManager] Database initialized');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        if (!db.objectStoreNames.contains(QUEUE_STORE_NAME)) {
          const objectStore = db.createObjectStore(QUEUE_STORE_NAME, {
            keyPath: 'id',
            autoIncrement: true
          });

          objectStore.createIndex('timestamp', 'timestamp', { unique: false });
          objectStore.createIndex('retryCount', 'retryCount', { unique: false });
          objectStore.createIndex('status', 'status', { unique: false });

          console.log('[QueueManager] Object store created');
        }
      };
    });
  }

  /**
   * Add request to upload queue
   */
  async enqueue(requestData) {
    await this.ensureDB();

    const queueItem = {
      ...requestData,
      status: 'pending',
      retryCount: 0,
      queuedAt: Date.now(),
      lastAttempt: null,
      error: null
    };

    const transaction = this.db.transaction([QUEUE_STORE_NAME], 'readwrite');
    const store = transaction.objectStore(QUEUE_STORE_NAME);

    return new Promise((resolve, reject) => {
      const request = store.add(queueItem);

      request.onsuccess = () => {
        console.log('[QueueManager] Item queued:', request.result);
        resolve(request.result);
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all pending items in queue
   */
  async getPending() {
    await this.ensureDB();

    const transaction = this.db.transaction([QUEUE_STORE_NAME], 'readonly');
    const store = transaction.objectStore(QUEUE_STORE_NAME);
    const index = store.index('status');

    return new Promise((resolve, reject) => {
      const request = index.getAll('pending');

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get queue stats
   */
  async getStats() {
    await this.ensureDB();

    const transaction = this.db.transaction([QUEUE_STORE_NAME], 'readonly');
    const store = transaction.objectStore(QUEUE_STORE_NAME);

    return new Promise((resolve, reject) => {
      const request = store.getAll();

      request.onsuccess = () => {
        const items = request.result;
        const stats = {
          total: items.length,
          pending: items.filter((i) => i.status === 'pending').length,
          processing: items.filter((i) => i.status === 'processing').length,
          completed: items.filter((i) => i.status === 'completed').length,
          failed: items.filter((i) => i.status === 'failed').length
        };
        resolve(stats);
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Process queue - attempt to upload all pending items
   */
  async processQueue() {
    if (this.isProcessing) {
      console.log('[QueueManager] Already processing queue');
      return;
    }

    this.isProcessing = true;
    console.log('[QueueManager] Processing queue...');

    try {
      const pending = await this.getPending();

      console.log(`[QueueManager] Found ${pending.length} pending items`);

      for (const item of pending) {
        await this.processItem(item);
      }

      console.log('[QueueManager] Queue processing complete');
    } catch (error) {
      console.error('[QueueManager] Queue processing failed:', error);
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Process single queue item
   */
  async processItem(item) {
    console.log(`[QueueManager] Processing item ${item.id}`);

    // Update status to processing
    await this.updateItem(item.id, {
      status: 'processing',
      lastAttempt: Date.now()
    });

    try {
      // Reconstruct request
      const requestInit = {
        method: item.method,
        headers: item.headers
      };

      if (item.body) {
        requestInit.body = item.body;
      }

      // Attempt upload
      const response = await fetch(item.url, requestInit);

      if (response.ok) {
        // Success - mark as completed
        console.log(`[QueueManager] Item ${item.id} uploaded successfully`);
        await this.updateItem(item.id, {
          status: 'completed',
          completedAt: Date.now()
        });

        // Parse response for transcription
        try {
          const data = await response.json();
          if (data.transcription) {
            // Notify UI about successful upload with transcription
            this.notifyUI('UPLOAD_SUCCESS', {
              itemId: item.id,
              transcription: data.transcription
            });
          }
        } catch (e) {
          // Response not JSON, ignore
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error(`[QueueManager] Item ${item.id} failed:`, error.message);

      // Increment retry count
      const newRetryCount = (item.retryCount || 0) + 1;

      if (newRetryCount >= MAX_RETRY_ATTEMPTS) {
        // Max retries exceeded - mark as failed
        await this.updateItem(item.id, {
          status: 'failed',
          retryCount: newRetryCount,
          error: error.message,
          failedAt: Date.now()
        });

        console.log(`[QueueManager] Item ${item.id} permanently failed`);
      } else {
        // Schedule retry with exponential backoff
        const retryDelay = INITIAL_RETRY_DELAY * Math.pow(2, newRetryCount);

        await this.updateItem(item.id, {
          status: 'pending',
          retryCount: newRetryCount,
          error: error.message,
          nextRetry: Date.now() + retryDelay
        });

        console.log(
          `[QueueManager] Item ${item.id} will retry in ${retryDelay}ms (attempt ${newRetryCount}/${MAX_RETRY_ATTEMPTS})`
        );
      }
    }
  }

  /**
   * Update queue item
   */
  async updateItem(id, updates) {
    await this.ensureDB();

    const transaction = this.db.transaction([QUEUE_STORE_NAME], 'readwrite');
    const store = transaction.objectStore(QUEUE_STORE_NAME);

    return new Promise((resolve, reject) => {
      const getRequest = store.get(id);

      getRequest.onsuccess = () => {
        const item = getRequest.result;
        if (!item) {
          reject(new Error('Item not found'));
          return;
        }

        const updatedItem = { ...item, ...updates };
        const putRequest = store.put(updatedItem);

        putRequest.onsuccess = () => resolve(putRequest.result);
        putRequest.onerror = () => reject(putRequest.error);
      };

      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  /**
   * Delete completed items older than 24 hours
   */
  async cleanupOldItems() {
    await this.ensureDB();

    const cutoff = Date.now() - 24 * 60 * 60 * 1000; // 24 hours ago

    const transaction = this.db.transaction([QUEUE_STORE_NAME], 'readwrite');
    const store = transaction.objectStore(QUEUE_STORE_NAME);

    const request = store.getAll();

    request.onsuccess = () => {
      const items = request.result;
      const toDelete = items.filter(
        (item) =>
          item.status === 'completed' &&
          item.completedAt &&
          item.completedAt < cutoff
      );

      toDelete.forEach((item) => {
        store.delete(item.id);
      });

      if (toDelete.length > 0) {
        console.log(`[QueueManager] Cleaned up ${toDelete.length} old items`);
      }
    };
  }

  /**
   * Clear entire queue
   */
  async clearQueue() {
    await this.ensureDB();

    const transaction = this.db.transaction([QUEUE_STORE_NAME], 'readwrite');
    const store = transaction.objectStore(QUEUE_STORE_NAME);

    return new Promise((resolve, reject) => {
      const request = store.clear();

      request.onsuccess = () => {
        console.log('[QueueManager] Queue cleared');
        resolve();
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Notify UI about events
   */
  notifyUI(type, data) {
    window.dispatchEvent(
      new CustomEvent('queuemanager', {
        detail: { type, data }
      })
    );
  }

  /**
   * Ensure database is initialized
   */
  async ensureDB() {
    if (!this.db) {
      await this.initDB();
    }
  }
}

// Create global instance
const queueManager = new QueueManager();

// Listen for service worker messages
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('message', async (event) => {
    console.log('[QueueManager] Service worker message:', event.data);

    if (event.data.type === 'QUEUE_REQUEST') {
      await queueManager.enqueue(event.data.data);
    }

    if (event.data.type === 'PROCESS_QUEUE') {
      await queueManager.processQueue();
    }
  });
}

// Auto-cleanup on page load
window.addEventListener('load', () => {
  queueManager.cleanupOldItems();
});

// Export for use in other scripts
window.queueManager = queueManager;

console.log('[QueueManager] Initialized');
