import json
from typing import List
from datetime import datetime
from jinja2 import Template
from find_impact.config import Config
from find_impact.models import ContentItem

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ developer_name }} - FindImpact Dashboard</title>
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #0c0a0f;
            --card-bg: rgba(20, 16, 28, 0.6);
            --card-border: rgba(255, 255, 255, 0.06);
            --text-primary: #f4f4f7;
            --text-secondary: #94a3b8;
            --primary: #8b5cf6;
            --primary-glow: rgba(139, 92, 246, 0.15);
            
            --github-color: #a78bfa;
            --youtube-color: #ef4444;
            --stackoverflow-color: #f97316;
            --medium-color: #10b981;
            --rss-color: #3b82f6;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(59, 130, 246, 0.08) 0%, transparent 40%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2rem 1rem;
            overflow-x: hidden;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        /* Glassmorphism Panel Common Style */
        .glass-panel {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Header section */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 2rem;
            margin-bottom: 2rem;
            position: relative;
        }

        header::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 5%;
            right: 5%;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--card-border), transparent);
        }

        .header-title h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff 30%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
            margin-bottom: 0.2rem;
        }

        .header-title p {
            font-size: 1rem;
            color: var(--text-secondary);
            font-weight: 400;
        }

        .header-meta {
            text-align: right;
        }

        .badge-devrel {
            background: var(--primary-glow);
            border: 1px solid var(--primary);
            color: #c084fc;
            padding: 0.4rem 1rem;
            border-radius: 30px;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            box-shadow: 0 0 15px var(--primary-glow);
            display: inline-block;
        }

        .last-updated {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
            font-style: italic;
        }

        /* Grid metrics */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            padding: 1.5rem;
            text-align: center;
            position: relative;
            overflow: hidden;
            cursor: pointer;
        }

        .metric-card:hover {
            transform: translateY(-5px);
            border-color: rgba(255, 255, 255, 0.15);
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
        }

        .metric-card.github::before { background: var(--github-color); }
        .metric-card.youtube::before { background: var(--youtube-color); }
        .metric-card.stackoverflow::before { background: var(--stackoverflow-color); }
        .metric-card.medium::before { background: var(--medium-color); }
        .metric-card.total::before { background: var(--primary); }

        .metric-card.github:hover { box-shadow: 0 10px 25px -5px rgba(167, 139, 250, 0.15); }
        .metric-card.youtube:hover { box-shadow: 0 10px 25px -5px rgba(239, 68, 68, 0.15); }
        .metric-card.stackoverflow:hover { box-shadow: 0 10px 25px -5px rgba(249, 115, 22, 0.15); }
        .metric-card.medium:hover { box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.15); }
        .metric-card.total:hover { box-shadow: 0 10px 25px -5px rgba(139, 92, 246, 0.15); }

        .metric-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }

        .metric-val {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 700;
            color: #ffffff;
            line-height: 1;
        }

        /* Charts Section */
        .charts-section {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        @media (max-width: 768px) {
            .charts-section {
                grid-template-columns: 1fr;
            }
            header {
                flex-direction: column;
                text-align: center;
                gap: 1.5rem;
            }
            .header-meta {
                text-align: center;
            }
        }

        .chart-box {
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 320px;
        }

        .chart-box h3 {
            font-family: 'Outfit', sans-serif;
            font-size: 1.1rem;
            align-self: flex-start;
            margin-bottom: 1rem;
            font-weight: 600;
            color: #ffffff;
        }

        .chart-container {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Control Panel */
        .control-panel {
            padding: 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
            align-items: center;
            justify-content: space-between;
        }

        .search-box {
            position: relative;
            flex-grow: 1;
            max-width: 450px;
            min-width: 250px;
        }

        .search-box input {
            width: 100%;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 0.8rem 1rem 0.8rem 2.5rem;
            color: var(--text-primary);
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s ease;
        }

        .search-box input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 15px rgba(139, 92, 246, 0.15);
            background: rgba(255, 255, 255, 0.07);
        }

        .search-box svg {
            position: absolute;
            left: 0.9rem;
            top: 50%;
            transform: translateY(-50%);
            fill: var(--text-secondary);
            width: 1.1rem;
            height: 1.1rem;
            pointer-events: none;
        }

        .filter-buttons {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .filter-btn {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            padding: 0.6rem 1.2rem;
            border-radius: 10px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .filter-btn:hover {
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-primary);
            border-color: rgba(255, 255, 255, 0.15);
        }

        .filter-btn.active {
            background: var(--primary-glow);
            color: #ffffff;
            border-color: var(--primary);
            box-shadow: 0 0 12px var(--primary-glow);
        }

        /* Items Grid */
        .items-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.2rem;
            margin-bottom: 4rem;
        }

        .content-card {
            display: grid;
            grid-template-columns: auto 1fr auto;
            gap: 1.5rem;
            padding: 1.5rem;
            align-items: center;
        }

        .content-card:hover {
            transform: scale(1.01);
            border-color: rgba(255, 255, 255, 0.12);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }

        .card-icon {
            width: 50px;
            height: 50px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--card-border);
        }

        .content-card.github .card-icon { background: rgba(167, 139, 250, 0.08); border-color: rgba(167, 139, 250, 0.2); }
        .content-card.youtube .card-icon { background: rgba(239, 68, 68, 0.08); border-color: rgba(239, 68, 68, 0.2); }
        .content-card.stackoverflow .card-icon { background: rgba(249, 115, 22, 0.08); border-color: rgba(249, 115, 22, 0.2); }
        .content-card.medium .card-icon { background: rgba(16, 185, 129, 0.08); border-color: rgba(16, 185, 129, 0.2); }
        .content-card.rss .card-icon { background: rgba(59, 130, 246, 0.08); border-color: rgba(59, 130, 246, 0.2); }

        .card-body {
            min-width: 0; /* Enable text truncation */
        }

        .card-meta {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-bottom: 0.4rem;
            font-size: 0.8rem;
        }

        .card-platform-badge {
            text-transform: uppercase;
            font-weight: 700;
            font-size: 0.7rem;
            letter-spacing: 0.05em;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
        }

        .github .card-platform-badge { background: rgba(167, 139, 250, 0.15); color: var(--github-color); }
        .youtube .card-platform-badge { background: rgba(239, 68, 68, 0.15); color: var(--youtube-color); }
        .stackoverflow .card-platform-badge { background: rgba(249, 115, 22, 0.15); color: var(--stackoverflow-color); }
        .medium .card-platform-badge { background: rgba(16, 185, 129, 0.15); color: var(--medium-color); }
        .rss .card-platform-badge { background: rgba(59, 130, 246, 0.15); color: var(--rss-color); }

        .card-date {
            color: var(--text-secondary);
        }

        .card-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 0.4rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .card-summary {
            font-size: 0.9rem;
            color: var(--text-secondary);
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .card-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .card-metrics {
            display: flex;
            gap: 0.8rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .metric-tag {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--card-border);
            padding: 0.3rem 0.7rem;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }

        .metric-tag svg {
            width: 14px;
            height: 14px;
            fill: var(--text-secondary);
        }

        .btn-visit {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: #ffffff;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            transition: all 0.2s ease;
        }

        .btn-visit:hover {
            background: var(--primary);
            border-color: var(--primary);
            box-shadow: 0 0 12px var(--primary-glow);
            transform: scale(1.1);
        }

        .btn-visit svg {
            width: 16px;
            height: 16px;
            fill: #ffffff;
        }

        /* YouTube specific Thumbnail style inside feed if available */
        .yt-thumb-container {
            width: 120px;
            height: 68px;
            border-radius: 8px;
            overflow: hidden;
            position: relative;
            border: 1px solid var(--card-border);
        }

        .yt-thumb-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }

        .content-card:hover .yt-thumb-container img {
            transform: scale(1.1);
        }

        @media (max-width: 650px) {
            .content-card {
                grid-template-columns: 1fr;
                text-align: center;
                gap: 1rem;
            }
            .card-icon, .yt-thumb-container {
                margin: 0 auto;
            }
            .card-meta {
                justify-content: center;
            }
            .card-actions {
                justify-content: center;
                flex-direction: column;
                gap: 0.8rem;
            }
        }

        .no-results {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Dashboard Header -->
        <header class="glass-panel">
            <div class="header-title">
                <h1>{{ developer_name }}</h1>
                <p>{{ developer_role }} @ {{ developer_company }}</p>
            </div>
            <div class="header-meta">
                <span class="badge-devrel">FindImpact Active</span>
                <p class="last-updated">Compiled: {{ generated_at }}</p>
            </div>
        </header>

        <!-- KPI Metrics Grid -->
        <section class="metrics-grid">
            <div class="glass-panel metric-card total" onclick="setFilter('all')">
                <p class="metric-title">Aggregate Reach</p>
                <p class="metric-val" id="cnt-total">0</p>
            </div>
            <div class="glass-panel metric-card github" onclick="setFilter('github')">
                <p class="metric-title">GitHub Items</p>
                <p class="metric-val" id="cnt-github">0</p>
            </div>
            <div class="glass-panel metric-card youtube" onclick="setFilter('youtube')">
                <p class="metric-title">YouTube Videos</p>
                <p class="metric-val" id="cnt-youtube">0</p>
            </div>
            <div class="glass-panel metric-card stackoverflow" onclick="setFilter('stackoverflow')">
                <p class="metric-title">StackOverflow Answers</p>
                <p class="metric-val" id="cnt-stackoverflow">0</p>
            </div>
            <div class="glass-panel metric-card medium" onclick="setFilter('medium')">
                <p class="metric-title">Medium Articles</p>
                <p class="metric-val" id="cnt-medium">0</p>
            </div>
        </section>

        <!-- Charts Dashboard -->
        <section class="charts-section">
            <div class="glass-panel chart-box">
                <h3>Platform Share</h3>
                <div class="chart-container">
                    <canvas id="shareChart"></canvas>
                </div>
            </div>
            <div class="glass-panel chart-box">
                <h3>Activity Over Time</h3>
                <div class="chart-container">
                    <canvas id="timelineChart"></canvas>
                </div>
            </div>
        </section>

        <!-- Search and Filters Control Panel -->
        <section class="glass-panel control-panel">
            <div class="search-box">
                <svg viewBox="0 0 24 24">
                    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
                <input type="text" id="searchInput" placeholder="Search title, description, or tag..." oninput="handleSearch()">
            </div>
            <div class="filter-buttons">
                <button class="filter-btn active" id="btn-all" onclick="setFilter('all')">All</button>
                <button class="filter-btn" id="btn-github" onclick="setFilter('github')">GitHub</button>
                <button class="filter-btn" id="btn-youtube" onclick="setFilter('youtube')">YouTube</button>
                <button class="filter-btn" id="btn-stackoverflow" onclick="setFilter('stackoverflow')">Stack Overflow</button>
                <button class="filter-btn" id="btn-medium" onclick="setFilter('medium')">Medium</button>
                <button class="filter-btn" id="btn-rss" onclick="setFilter('rss')">RSS Feeds</button>
            </div>
        </section>

        <!-- Contribution Feed -->
        <section class="items-grid" id="itemsGrid">
            <!-- Rendered dynamically by client-side javascript -->
        </section>
    </div>

    <!-- Client-side script -->
    <script>
        // Injecting the raw content items data directly into JS from python
        const contentData = {{ content_items_json }};
        
        let currentFilter = 'all';
        let searchQuery = '';
        let shareChart = null;
        let timelineChart = null;

        // Populate KPIs initially
        function calculateKPIs() {
            const counts = { github: 0, youtube: 0, stackoverflow: 0, medium: 0, rss: 0 };
            contentData.forEach(item => {
                if (counts[item.platform] !== undefined) {
                    counts[item.platform]++;
                }
            });
            document.getElementById('cnt-total').innerText = contentData.length;
            document.getElementById('cnt-github').innerText = counts.github;
            document.getElementById('cnt-youtube').innerText = counts.youtube;
            document.getElementById('cnt-stackoverflow').innerText = counts.stackoverflow;
            document.getElementById('cnt-medium').innerText = counts.medium;
        }

        // Filter and Search items
        function getFilteredItems() {
            return contentData.filter(item => {
                const matchesPlatform = (currentFilter === 'all' || item.platform === currentFilter);
                
                const searchContent = (
                    item.title + " " + 
                    (item.summary || "") + " " + 
                    (item.platform || "") + " " +
                    JSON.stringify(item.extra_metadata || {})
                ).toLowerCase();
                
                const matchesSearch = searchQuery === '' || searchContent.includes(searchQuery.toLowerCase());
                
                return matchesPlatform && matchesSearch;
            });
        }

        // Render Cards
        function renderItems() {
            const grid = document.getElementById('itemsGrid');
            grid.innerHTML = '';
            
            const filtered = getFilteredItems();
            
            if (filtered.length === 0) {
                grid.innerHTML = `<div class="glass-panel no-results">No tracked contributions found matching filters.</div>`;
                return;
            }

            filtered.forEach(item => {
                const card = document.createElement('div');
                card.className = `glass-panel content-card ${item.platform}`;
                
                // Formatted date
                let dateStr = "Unknown Date";
                if (item.publish_date) {
                    const date = new Date(item.publish_date);
                    if (!isNaN(date.getTime())) {
                        dateStr = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
                    }
                }

                // Platform specific rendering detail
                let iconHtml = '📄';
                let visualEl = '';
                let metricsHtml = '';

                if (item.platform === 'github') {
                    iconHtml = `
                        <svg width="24" height="24" fill="#a78bfa" viewBox="0 0 24 24">
                            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.182-1.304.347-1.604-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                        </svg>
                    `;
                    const type = item.extra_metadata.type || 'commit';
                    iconHtml = `<div class="card-icon">${iconHtml}</div>`;
                    
                    if (type === 'pull_request') {
                        metricsHtml = `
                            <div class="metric-tag">PR #${item.extra_metadata.pr_number || ''}</div>
                            ${item.metrics.additions ? `<div class="metric-tag" style="color: #10b981">+${item.metrics.additions}</div>` : ''}
                            ${item.metrics.deletions ? `<div class="metric-tag" style="color: #ef4444">-${item.metrics.deletions}</div>` : ''}
                        `;
                    } else if (type === 'commit') {
                        metricsHtml = `<div class="metric-tag">Commit ${item.extra_metadata.sha ? item.extra_metadata.sha.substring(0,7) : ''}</div>`;
                    }
                } else if (item.platform === 'youtube') {
                    iconHtml = `
                        <svg width="24" height="24" fill="#ef4444" viewBox="0 0 24 24">
                            <path d="M23.498 6.163c-.272-.98-1.09-1.755-2.093-2.025C19.562 3.6 12 3.6 12 3.6s-7.562 0-9.405.538C1.59 4.408.773 5.183.5 6.163.025 7.975 0 11.785 0 11.785s.025 3.81.5 5.622c.272.98 1.09 1.758 2.093 2.028C4.438 19.97 12 19.97 12 19.97s7.562 0 9.405-.538c1.003-.27 1.82-.1.045-2.028.475-1.812.5-5.622.5-5.622s-.025-3.81-.5-5.622zM9.545 15.568V8.01L15.818 11.79l-6.273 3.778z"/>
                        </svg>
                    `;
                    iconHtml = `<div class="card-icon">${iconHtml}</div>`;
                    
                    if (item.extra_metadata.thumbnail_url) {
                        visualEl = `
                            <div class="yt-thumb-container">
                                <img src="${item.extra_metadata.thumbnail_url}" alt="Thumbnail">
                            </div>
                        `;
                    }
                    metricsHtml = `<div class="metric-tag">${item.extra_metadata.channel_title || 'YouTube'}</div>`;
                } else if (item.platform === 'stackoverflow') {
                    iconHtml = `
                        <svg width="24" height="24" fill="#f97316" viewBox="0 0 24 24">
                            <path d="M18.986 21.865v-6.404h2.134V24H1.844v-8.539h2.13v6.404h15.012zM6.111 17.05l10.3-.406.037 2.13-10.3.408-.037-2.132zm.543-4.525l9.96 3.19.646-2.03-9.96-3.19-.646 2.03zm1.61-4.225l8.77 5.67 1.155-1.784-8.77-5.67-1.155 1.784zm2.846-3.556l6.83 7.91 1.62-1.393-6.83-7.91-1.62 1.393zm4.275-2.22l4.28 9.53 1.944-.875-4.28-9.53-1.944.875z"/>
                        </svg>
                    `;
                    iconHtml = `<div class="card-icon">${iconHtml}</div>`;
                    
                    const score = item.metrics.score || 0;
                    const isAccepted = item.metrics.is_accepted;
                    metricsHtml = `
                        <div class="metric-tag" style="${isAccepted ? 'border-color: #10b981; color: #10b981' : ''}">
                            Score: ${score} ${isAccepted ? '✔' : ''}
                        </div>
                    `;
                } else if (item.platform === 'medium') {
                    iconHtml = `
                        <svg width="24" height="24" fill="#10b981" viewBox="0 0 24 24">
                            <path d="M13.54 12a6.8 6.8 0 11-13.54 0 6.8 6.8 0 0113.54 0zM24 12c0 3.535-1.516 6.4-3.385 6.4s-3.387-2.865-3.387-6.4 1.518-6.4 3.387-6.4S24 8.465 24 12zm-6.217 0c0 3.125-.328 5.66-1.733 5.66s-1.731-2.535-1.731-5.66.326-5.66 1.731-5.66 1.733 2.535 1.733 5.66z"/>
                        </svg>
                    `;
                    iconHtml = `<div class="card-icon">${iconHtml}</div>`;
                    if (item.extra_metadata.author) {
                        metricsHtml = `<div class="metric-tag">Author: ${item.extra_metadata.author}</div>`;
                    }
                } else {
                    iconHtml = `<div class="card-icon">📰</div>`;
                    metricsHtml = `<div class="metric-tag">${item.extra_metadata.feed_name || 'RSS'}</div>`;
                }

                card.innerHTML = `
                    ${visualEl ? visualEl : iconHtml}
                    <div class="card-body">
                        <div class="card-meta">
                            <span class="card-platform-badge">${item.platform}</span>
                            <span class="card-date">${dateStr}</span>
                        </div>
                        <h4 class="card-title" title="${item.title.replace(/\[.*?\]\s*/, '')}">${item.title.replace(/\[.*?\]\s*/, '')}</h4>
                        <p class="card-summary">${item.summary || 'No description summary available.'}</p>
                    </div>
                    <div class="card-actions">
                        <div class="card-metrics">
                            ${metricsHtml}
                        </div>
                        <a href="${item.url}" target="_blank" class="btn-visit" title="Open Content Link">
                            <svg viewBox="0 0 24 24">
                                <path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/>
                            </svg>
                        </a>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        // Handle text searches
        function handleSearch() {
            searchQuery = document.getElementById('searchInput').value;
            renderItems();
        }

        // Handle filter clicks
        function setFilter(platform) {
            currentFilter = platform;
            
            // Toggle active classes
            const btns = ['all', 'github', 'youtube', 'stackoverflow', 'medium', 'rss'];
            btns.forEach(b => {
                const btn = document.getElementById(`btn-${b}`);
                if (btn) {
                    if (b === platform) btn.classList.add('active');
                    else btn.classList.remove('active');
                }
            });

            renderItems();
        }

        // Initialize Graphs using ChartJS
        function renderCharts() {
            const counts = { github: 0, youtube: 0, stackoverflow: 0, medium: 0, rss: 0 };
            
            // Time aggregations
            const timelineData = {}; // Month-Year string -> count
            
            contentData.forEach(item => {
                if (counts[item.platform] !== undefined) {
                    counts[item.platform]++;
                } else {
                    counts.rss++;
                }

                if (item.publish_date) {
                    const d = new Date(item.publish_date);
                    if (!isNaN(d.getTime())) {
                        const monthYear = d.toLocaleString('default', { month: 'short', year: 'numeric' });
                        // To sort easily, map sorting value
                        const sortVal = d.getFullYear() * 12 + d.getMonth();
                        if (!timelineData[monthYear]) {
                            timelineData[monthYear] = { count: 0, sort: sortVal };
                        }
                        timelineData[monthYear].count++;
                    }
                }
            });

            // 1. Platform Share Chart
            const ctxShare = document.getElementById('shareChart').getContext('2d');
            shareChart = new Chart(ctxShare, {
                type: 'doughnut',
                data: {
                    labels: ['GitHub', 'YouTube', 'Stack Overflow', 'Medium', 'RSS'],
                    datasets: [{
                        data: [counts.github, counts.youtube, counts.stackoverflow, counts.medium, counts.rss],
                        backgroundColor: ['#a78bfa', '#ef4444', '#f97316', '#10b981', '#3b82f6'],
                        borderColor: '#0c0a0f',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
                        }
                    }
                }
            });

            // 2. Timeline Chart (sorted chronologically)
            const sortedTimeline = Object.entries(timelineData)
                .sort((a, b) => a[1].sort - b[1].sort)
                .slice(-10); // Display last 10 active months
                
            const labels = sortedTimeline.map(e => e[0]);
            const values = sortedTimeline.map(e => e[1].count);

            const ctxTimeline = document.getElementById('timelineChart').getContext('2d');
            timelineChart = new Chart(ctxTimeline, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Contributions',
                        data: values,
                        backgroundColor: 'rgba(139, 92, 246, 0.4)',
                        borderColor: '#8b5cf6',
                        borderWidth: 2,
                        borderRadius: 6,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } }
                        },
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.04)' },
                            ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 }, stepSize: 1 }
                        }
                    }
                }
            });
        }

        // Run setup
        window.addEventListener('DOMContentLoaded', () => {
            calculateKPIs();
            renderCharts();
            renderItems();
        });
    </script>
</body>
</html>
"""


class HTMLExporter:
    def export(self, config: Config, items: List[ContentItem]):
        """Generates a stunning, self-contained interactive web dashboard."""
        path = config.html_report_path
        print(f"Generating premium interactive HTML dashboard: {path}...")

        # Prepare serializable content list sorted by date descending
        sorted_items = sorted(items, key=lambda x: x.parsed_date, reverse=True)
        items_dict_list = [item.to_dict() for item in sorted_items]
        content_items_json = json.dumps(items_dict_list, ensure_ascii=False)

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Compile Jinja template
        try:
            t = Template(HTML_TEMPLATE)
            rendered_html = t.render(
                developer_name=config.developer_name,
                developer_role=config.developer_role,
                developer_company=config.developer_company,
                generated_at=generated_at,
                content_items_json=content_items_json,
            )

            with open(path, "w", encoding="utf-8") as f:
                f.write(rendered_html)

            print("HTML Dashboard exported successfully.")
        except Exception as e:
            print(f"Error compiling HTML dashboard: {e}")
            raise e
