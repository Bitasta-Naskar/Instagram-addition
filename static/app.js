/**
 * Instagram Activity Tracker Frontend Application
 * Handles tab switching, data fetching, like/save toggling,
 * and automatic real-time updates for the "Visited Profiles" section.
 */

// Application State
const state = {
  activeTab: 'visited',
  visitedProfiles: [],
  likedPosts: [],
  savedPosts: [],
  allPosts: [],
  visitedSearchTerm: ''
};

// DOM Elements
const elements = {
  tabButtons: document.querySelectorAll('.tab-button'),
  panels: {
    visited: document.getElementById('panel-visited'),
    liked: document.getElementById('panel-liked'),
    saved: document.getElementById('panel-saved'),
    feed: document.getElementById('panel-feed')
  },
  counts: {
    visited: document.getElementById('count-visited'),
    liked: document.getElementById('count-liked'),
    saved: document.getElementById('count-saved'),
    feed: document.getElementById('count-all-posts')
  },
  visitedList: document.getElementById('visitedProfilesList'),
  visitedEmpty: document.getElementById('visitedEmptyState'),
  visitedSearch: document.getElementById('visitedSearchInput'),
  visitedSummary: document.getElementById('visitedSummaryText'),
  likedList: document.getElementById('likedPostsList'),
  likedEmpty: document.getElementById('likedEmptyState'),
  savedList: document.getElementById('savedPostsList'),
  savedEmpty: document.getElementById('savedEmptyState'),
  feedList: document.getElementById('feedPostsList'),
  btnReset: document.getElementById('btnResetData'),
  toast: document.getElementById('toastNotification')
};

// SVG Icons
const ICONS = {
  heartFilled: `<svg class="action-icon" viewBox="0 0 24 24" fill="#ed4956" stroke="#ed4956"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`,
  heartOutline: `<svg class="action-icon" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`,
  bookmarkFilled: `<svg class="action-icon" viewBox="0 0 24 24" fill="#262626" stroke="#262626"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>`,
  bookmarkOutline: `<svg class="action-icon" viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>`
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadAllData();
});

// Setup event listeners
function setupEventListeners() {
  // Tab navigation
  elements.tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      switchTab(tab);
    });
  });

  // Search filter for visited profiles
  elements.visitedSearch.addEventListener('input', (e) => {
    state.visitedSearchTerm = e.target.value.toLowerCase().trim();
    renderVisitedProfiles();
  });

  // Reset database button
  elements.btnReset.addEventListener('click', handleResetData);
}

// Switch Tab
function switchTab(tabName) {
  state.activeTab = tabName;

  elements.tabButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });

  Object.entries(elements.panels).forEach(([name, panel]) => {
    panel.classList.toggle('active', name === tabName);
  });
}
window.switchTab = switchTab;

// Show Toast message
let toastTimeout;
function showToast(message) {
  clearTimeout(toastTimeout);
  elements.toast.textContent = message;
  elements.toast.classList.remove('hidden');
  toastTimeout = setTimeout(() => {
    elements.toast.classList.add('hidden');
  }, 2800);
}

// Fetch all activity data from server
async function loadAllData() {
  try {
    const [visitedRes, likedRes, savedRes, allRes] = await Promise.all([
      fetch('/api/activity/visited-profiles').then(r => r.json()),
      fetch('/api/activity/liked').then(r => r.json()),
      fetch('/api/activity/saved').then(r => r.json()),
      fetch('/api/posts').then(r => r.json())
    ]);

    state.visitedProfiles = visitedRes.data || [];
    state.likedPosts = likedRes.data || [];
    state.savedPosts = savedRes.data || [];
    state.allPosts = allRes.data || [];

    updateCounts();
    renderAllPanels();
  } catch (err) {
    console.error('Failed to load activity data:', err);
    showToast('Failed to load data. Please refresh.');
  }
}

// Update count badges on tabs
function updateCounts() {
  elements.counts.visited.textContent = state.visitedProfiles.length;
  elements.counts.liked.textContent = state.likedPosts.length;
  elements.counts.saved.textContent = state.savedPosts.length;
  elements.counts.feed.textContent = state.allPosts.length;
}

// Render all panels
function renderAllPanels() {
  renderVisitedProfiles();
  renderLikedPosts();
  renderSavedPosts();
  renderFeedPosts();
}

// Render Visited Profiles section
function renderVisitedProfiles() {
  const filtered = state.visitedProfiles.filter(p => {
    if (!state.visitedSearchTerm) return true;
    return (
      p.username.toLowerCase().includes(state.visitedSearchTerm) ||
      p.full_name.toLowerCase().includes(state.visitedSearchTerm)
    );
  });

  elements.visitedSummary.textContent = `${state.visitedProfiles.length} account${state.visitedProfiles.length === 1 ? '' : 's'} visited`;

  if (state.visitedProfiles.length === 0) {
    elements.visitedList.innerHTML = '';
    elements.visitedEmpty.classList.remove('hidden');
    return;
  }

  elements.visitedEmpty.classList.add('hidden');

  if (filtered.length === 0) {
    elements.visitedList.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: var(--text-secondary);">
        No profiles match "${state.visitedSearchTerm}"
      </div>
    `;
    return;
  }

  elements.visitedList.innerHTML = filtered.map(profile => {
    let badgeClass = profile.interaction_type;
    let badgeText = profile.badge_label;
    let countsDesc = [];
    if (profile.liked_count > 0) countsDesc.push(`${profile.liked_count} liked post${profile.liked_count > 1 ? 's' : ''}`);
    if (profile.saved_count > 0) countsDesc.push(`${profile.saved_count} saved post${profile.saved_count > 1 ? 's' : ''}`);

    return `
      <article class="profile-card">
        <div class="profile-card-top">
          <div class="avatar-wrapper">
            <img class="avatar-img" src="${profile.avatar_url}" alt="${profile.username}" loading="lazy">
          </div>
          <div class="profile-info">
            <div class="profile-username">@${escapeHtml(profile.username)}</div>
            <div class="profile-fullname">${escapeHtml(profile.full_name)}</div>
          </div>
        </div>

        <p class="profile-bio">${escapeHtml(profile.bio || '')}</p>

        <div class="profile-card-footer">
          <span class="interaction-pill ${badgeClass}">
            ${badgeClass === 'liked' ? '💖' : badgeClass === 'saved' ? '🔖' : '💖🔖'}
            ${badgeText}
          </span>
          <span class="interaction-details">${countsDesc.join(' • ')}</span>
        </div>
      </article>
    `;
  }).join('');
}

// Render Liked Posts
function renderLikedPosts() {
  if (state.likedPosts.length === 0) {
    elements.likedList.innerHTML = '';
    elements.likedEmpty.classList.remove('hidden');
    return;
  }

  elements.likedEmpty.classList.add('hidden');
  elements.likedList.innerHTML = state.likedPosts.map(post => createPostCardHtml(post, 'liked')).join('');
}

// Render Saved Posts
function renderSavedPosts() {
  if (state.savedPosts.length === 0) {
    elements.savedList.innerHTML = '';
    elements.savedEmpty.classList.remove('hidden');
    return;
  }

  elements.savedEmpty.classList.add('hidden');
  elements.savedList.innerHTML = state.savedPosts.map(post => createPostCardHtml(post, 'saved')).join('');
}

// Render Explore Feed
function renderFeedPosts() {
  elements.feedList.innerHTML = state.allPosts.map(post => createPostCardHtml(post, 'feed')).join('');
}

// Helper to construct a post card
function createPostCardHtml(post, context) {
  const isLiked = post.is_liked === 1;
  const isSaved = post.is_saved === 1;
  const isTracked = isLiked || isSaved;

  return `
    <article class="post-card" data-post-id="${post.id}">
      <header class="post-header">
        <img class="post-author-avatar" src="${post.avatar_url}" alt="${post.username}" loading="lazy">
        <span class="post-author-name">@${escapeHtml(post.username)}</span>
      </header>

      <div class="post-image-container">
        <img class="post-img" src="${post.image_url}" alt="Post image" loading="lazy">
      </div>

      <div class="post-body">
        <div class="post-actions">
          <div class="post-actions-left">
            <button class="action-btn ${isLiked ? 'active-like' : ''}" 
                    onclick="handleToggleLike(${post.id}, '${context}')" 
                    title="${isLiked ? 'Unlike' : 'Like'}">
              ${isLiked ? ICONS.heartFilled : ICONS.heartOutline}
            </button>
          </div>
          <button class="action-btn ${isSaved ? 'active-save' : ''}" 
                  onclick="handleToggleSave(${post.id}, '${context}')" 
                  title="${isSaved ? 'Unsave' : 'Save'}">
            ${isSaved ? ICONS.bookmarkFilled : ICONS.bookmarkOutline}
          </button>
        </div>

        <p class="post-caption">
          <span class="username-bold">@${escapeHtml(post.username)}</span>
          ${escapeHtml(post.caption)}
        </p>

        <div class="post-tracking-status">
          <span class="status-dot ${isTracked ? 'tracked' : 'untracked'}"></span>
          <span>${isTracked ? 'Author tracked in Visited Profiles' : 'Not tracked (neither liked nor saved)'}</span>
        </div>
      </div>
    </article>
  `;
}

// Handle Toggle Like
async function handleToggleLike(postId, context) {
  try {
    const res = await fetch(`/api/posts/${postId}/toggle-like`, { method: 'POST' });
    const data = await res.json();
    if (!data.success) {
      showToast('Error updating like');
      return;
    }

    const post = data.post;
    const actionText = post.is_liked ? 'Liked' : 'Unliked';
    const statusNote = post.is_liked
      ? `• @${post.username} tracked in Visited Profiles`
      : (post.is_saved ? `• @${post.username} still saved` : `• @${post.username} removed from Visited Profiles`);

    showToast(`${actionText} post ${statusNote}`);
    await loadAllData();
  } catch (err) {
    console.error('Error toggling like:', err);
    showToast('Failed to update like');
  }
}
window.handleToggleLike = handleToggleLike;

// Handle Toggle Save
async function handleToggleSave(postId, context) {
  try {
    const res = await fetch(`/api/posts/${postId}/toggle-save`, { method: 'POST' });
    const data = await res.json();
    if (!data.success) {
      showToast('Error updating save');
      return;
    }

    const post = data.post;
    const actionText = post.is_saved ? 'Saved' : 'Removed from Saved';
    const statusNote = post.is_saved
      ? `• @${post.username} tracked in Visited Profiles`
      : (post.is_liked ? `• @${post.username} still liked` : `• @${post.username} removed from Visited Profiles`);

    showToast(`${actionText} ${statusNote}`);
    await loadAllData();
  } catch (err) {
    console.error('Error toggling save:', err);
    showToast('Failed to update save');
  }
}
window.handleToggleSave = handleToggleSave;

// Handle Reset Database
async function handleResetData() {
  if (!confirm('Reset sample accounts and posts to default state?')) return;
  try {
    const res = await fetch('/api/reset', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast('Sample database reset to default state');
      await loadAllData();
    }
  } catch (err) {
    console.error('Error resetting database:', err);
    showToast('Failed to reset database');
  }
}

// Helper: Escape HTML
function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
