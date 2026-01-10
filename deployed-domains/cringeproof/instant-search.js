/**
 * Instant Search - Game-Like Hide & Seek UI
 *
 * Features:
 * - Type-as-you-search (no Enter key needed)
 * - Debounced search with visual feedback
 * - Game-like particle effects
 * - Animated card reveals
 * - Keyboard navigation (arrow keys)
 * - Search result highlighting
 * - Real-time result count
 */

class InstantSearch {
  constructor(options = {}) {
    this.searchInput = options.searchInput || document.getElementById('instant-search');
    this.resultsContainer =
      options.resultsContainer || document.getElementById('search-results');
    this.debounceDelay = options.debounceDelay || 300;
    this.minChars = options.minChars || 2;
    this.maxResults = options.maxResults || 20;

    this.debounceTimer = null;
    this.currentQuery = '';
    this.selectedIndex = -1;
    this.results = [];

    this.init();
  }

  init() {
    if (!this.searchInput || !this.resultsContainer) {
      console.error('[InstantSearch] Missing search input or results container');
      return;
    }

    // Input event listener (debounced)
    this.searchInput.addEventListener('input', (e) => {
      this.handleInput(e.target.value);
    });

    // Keyboard navigation
    this.searchInput.addEventListener('keydown', (e) => {
      this.handleKeyboard(e);
    });

    // Click outside to close
    document.addEventListener('click', (e) => {
      if (!this.searchInput.contains(e.target) && !this.resultsContainer.contains(e.target)) {
        this.hideResults();
      }
    });

    console.log('[InstantSearch] Initialized');
  }

  /**
   * Handle input changes with debounce
   */
  handleInput(value) {
    clearTimeout(this.debounceTimer);

    this.currentQuery = value.trim();

    // Show loading state
    if (this.currentQuery.length >= this.minChars) {
      this.showLoading();
    } else {
      this.hideResults();
      return;
    }

    // Debounce search
    this.debounceTimer = setTimeout(() => {
      this.performSearch(this.currentQuery);
    }, this.debounceDelay);
  }

  /**
   * Perform search query
   */
  async performSearch(query) {
    try {
      console.log('[InstantSearch] Searching for:', query);

      // API call to search endpoint
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=${this.maxResults}`);

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`);
      }

      const data = await response.json();
      this.results = data.results || [];

      console.log('[InstantSearch] Found', this.results.length, 'results');

      // Render results with animation
      this.renderResults(this.results, query);

      // Dispatch search event
      window.dispatchEvent(
        new CustomEvent('instantsearch', {
          detail: { type: 'SEARCH_COMPLETE', query, results: this.results }
        })
      );
    } catch (error) {
      console.error('[InstantSearch] Search error:', error);
      this.showError(error.message);
    }
  }

  /**
   * Render search results with game-like animations
   */
  renderResults(results, query) {
    this.selectedIndex = -1;

    if (results.length === 0) {
      this.resultsContainer.innerHTML = `
        <div class="search-empty">
          <div class="search-empty-icon">🔍</div>
          <div class="search-empty-text">No ideas found for "${this.escapeHtml(query)}"</div>
          <div class="search-empty-hint">Try different keywords or browse all ideas</div>
        </div>
      `;
      this.resultsContainer.classList.add('search-results-visible');
      return;
    }

    // Build results HTML
    const resultsHTML = results
      .map((result, index) => {
        const highlightedTitle = this.highlightMatch(result.title, query);
        const highlightedText = this.highlightMatch(
          result.text.substring(0, 150) + '...',
          query
        );

        return `
        <div class="search-result-item" data-index="${index}" data-hash="${result.public_hash}">
          <div class="search-result-header">
            <div class="search-result-title">${highlightedTitle}</div>
            <div class="search-result-score">${result.score}/100</div>
          </div>
          <div class="search-result-text">${highlightedText}</div>
          <div class="search-result-meta">
            <span class="search-result-tier">${this.getTierEmoji(result.tier)} ${this.escapeHtml(result.tier)}</span>
            <span class="search-result-date">${new Date(result.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      `;
      })
      .join('');

    this.resultsContainer.innerHTML = `
      <div class="search-results-header">
        <span class="search-results-count">Found ${results.length} ${results.length === 1 ? 'idea' : 'ideas'}</span>
        <button class="search-results-close" onclick="instantSearch.hideResults()">✕</button>
      </div>
      <div class="search-results-list">
        ${resultsHTML}
      </div>
    `;

    // Add click handlers
    this.resultsContainer.querySelectorAll('.search-result-item').forEach((item, index) => {
      item.addEventListener('click', () => {
        this.selectResult(index);
      });

      item.addEventListener('mouseenter', () => {
        this.highlightResult(index);
      });
    });

    // Show with animation
    this.resultsContainer.classList.add('search-results-visible');

    // Staggered reveal animation
    this.resultsContainer.querySelectorAll('.search-result-item').forEach((item, index) => {
      item.style.animationDelay = `${index * 50}ms`;
    });
  }

  /**
   * Show loading state
   */
  showLoading() {
    this.resultsContainer.innerHTML = `
      <div class="search-loading">
        <div class="search-loading-spinner"></div>
        <div class="search-loading-text">Searching...</div>
      </div>
    `;
    this.resultsContainer.classList.add('search-results-visible');
  }

  /**
   * Show error state
   */
  showError(message) {
    this.resultsContainer.innerHTML = `
      <div class="search-error">
        <div class="search-error-icon">⚠️</div>
        <div class="search-error-text">Search failed: ${this.escapeHtml(message)}</div>
      </div>
    `;
    this.resultsContainer.classList.add('search-results-visible');
  }

  /**
   * Hide results
   */
  hideResults() {
    this.resultsContainer.classList.remove('search-results-visible');
    this.selectedIndex = -1;
  }

  /**
   * Handle keyboard navigation
   */
  handleKeyboard(e) {
    const items = this.resultsContainer.querySelectorAll('.search-result-item');

    if (items.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
        this.highlightResult(this.selectedIndex);
        break;

      case 'ArrowUp':
        e.preventDefault();
        this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
        if (this.selectedIndex === -1) {
          this.clearHighlight();
        } else {
          this.highlightResult(this.selectedIndex);
        }
        break;

      case 'Enter':
        e.preventDefault();
        if (this.selectedIndex >= 0) {
          this.selectResult(this.selectedIndex);
        }
        break;

      case 'Escape':
        e.preventDefault();
        this.hideResults();
        this.searchInput.blur();
        break;
    }
  }

  /**
   * Highlight result item
   */
  highlightResult(index) {
    this.selectedIndex = index;

    const items = this.resultsContainer.querySelectorAll('.search-result-item');
    items.forEach((item, i) => {
      if (i === index) {
        item.classList.add('search-result-selected');
        item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else {
        item.classList.remove('search-result-selected');
      }
    });
  }

  /**
   * Clear highlight
   */
  clearHighlight() {
    const items = this.resultsContainer.querySelectorAll('.search-result-item');
    items.forEach((item) => item.classList.remove('search-result-selected'));
  }

  /**
   * Select result and navigate
   */
  selectResult(index) {
    if (index < 0 || index >= this.results.length) return;

    const result = this.results[index];
    console.log('[InstantSearch] Selected:', result.title);

    // Navigate to idea page
    window.location.href = `/i/${result.public_hash}`;
  }

  /**
   * Highlight search matches
   */
  highlightMatch(text, query) {
    if (!query || query.length < 2) return this.escapeHtml(text);

    const escapedText = this.escapeHtml(text);
    const escapedQuery = this.escapeHtml(query);

    // Simple word-based highlighting
    const words = escapedQuery.split(/\s+/).filter((w) => w.length > 0);
    let highlighted = escapedText;

    words.forEach((word) => {
      const regex = new RegExp(`(${this.escapeRegex(word)})`, 'gi');
      highlighted = highlighted.replace(regex, '<mark>$1</mark>');
    });

    return highlighted;
  }

  /**
   * Get tier emoji
   */
  getTierEmoji(tier) {
    const emojis = {
      trash: '🗑️',
      bronze: '🥉',
      silver: '🥈',
      gold: '🥇',
      platinum: '💎'
    };
    return emojis[tier] || '📝';
  }

  /**
   * Escape HTML
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Escape regex special characters
   */
  escapeRegex(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
}

// Auto-initialize if search input exists
let instantSearch;

window.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('instant-search');
  const resultsContainer = document.getElementById('search-results');

  if (searchInput && resultsContainer) {
    instantSearch = new InstantSearch({
      searchInput,
      resultsContainer,
      debounceDelay: 300,
      minChars: 2,
      maxResults: 20
    });

    console.log('[InstantSearch] Ready');
  }
});

// Export for manual initialization
window.InstantSearch = InstantSearch;
