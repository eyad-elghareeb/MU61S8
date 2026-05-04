#!/usr/bin/env python3
"""
Admin Dashboard for Quiz Projects
===============================
A local Flask server providing a web-based admin interface for managing
quiz/bank files in static quiz sites (compatible with MU61S8/QuizTool).

Features:
- File tree explorer
- Embedded editing tools (reused from QuizTool)
- File/folder management
- Quiz ↔ Bank conversion
- Manual Git commit/push
- Auto-sync indexes

Requirements:
    pip install flask GitPython

Usage:
    cd your-quiz-project/
    python scripts/admin-dashboard.py

Then open http://localhost:5500/admin/ in your browser.
"""

import os
import json
import uuid
import shutil
import subprocess
import re
import threading
import webbrowser
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template_string

# Try to import GitPython
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("Warning: GitPython not installed. Git features will be disabled.")

app = Flask(__name__)

# Project root (where this script is run from)
PROJECT_ROOT = Path.cwd()

# Paths
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
SYNC_SCRIPT = SCRIPTS_DIR / 'sync_quiz_assets.py'
INDEX_TEMPLATE = PROJECT_ROOT / 'index-template.html'  # If available

# Dashboard HTML template
DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - {{ project_name }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0d1117;
            --surface: #161b22;
            --surface2: #1c2330;
            --border: #30363d;
            --text: #e6edf3;
            --text-muted: #8b949e;
            --accent: #f0a500;
            --accent-dim: rgba(240,165,0,0.12);
            --radius: 12px;
            --shadow: 0 4px 24px rgba(0,0,0,0.4);
            --wrong: #da3633;
            --wrong-bg: rgba(218,54,51,0.12);
            --flagged: #58a6ff;
            --flagged-bg: rgba(88,166,255,0.12);
            --correct: #2ea043;
            --correct-bg: rgba(46,160,67,0.12);
            --transition: 0.2s ease;
        }
        [data-theme="light"] {
            --bg: #f3f0eb;
            --surface: #ffffff;
            --surface2: #f8f6f1;
            --border: #d0ccc5;
            --text: #1c1917;
            --text-muted: #78716c;
            --accent: #c27803;
            --accent-dim: rgba(194,120,3,0.10);
            --shadow: 0 4px 24px rgba(0,0,0,0.10);
            --skip: #3b82f6;
            --correct-bg: rgba(34,197,94,0.12);
            --wrong-bg: rgba(239,68,68,0.12);
            --flagged-bg: rgba(59,130,246,0.12);
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--text); }
        .container { max-width: 1400px; margin: 0 auto; padding: 1rem; }
        .header { text-align: center; margin-bottom: 2rem; }
        .header h1 { font-family: 'Playfair Display', serif; font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header h1 span { color: var(--accent); }
        .header p { color: var(--text-muted); }
        .main-grid { display: grid; grid-template-columns: 1fr; gap: 1.5rem; height: auto; min-height: calc(100vh - 200px); }
        @media (min-width: 900px) {
            .main-grid { grid-template-columns: 320px 1fr; height: calc(100vh - 200px); }
        }
        .sidebar { background: var(--surface); border-radius: var(--radius); padding: 1.25rem; overflow-y: auto; border: 1px solid var(--border); box-shadow: var(--shadow); }
        .content { background: var(--surface); border-radius: var(--radius); padding: 1.5rem; overflow-y: auto; border: 1px solid var(--border); box-shadow: var(--shadow); display: flex; flex-direction: column; }
        .file-tree { list-style: none; }
        .file-tree li { margin: 0.25rem 0; }
        .file-tree .folder { cursor: pointer; font-weight: 600; color: var(--accent); }
        .file-tree .file { cursor: pointer; padding: 0.25rem; border-radius: 6px; }
        .file-tree .file:hover { background: var(--surface2); }
        .btn { padding: 0.75rem 1.2rem; border-radius: var(--radius); border: none; background: var(--accent); color: #000; cursor: pointer; font-weight: 700; transition: transform var(--transition), opacity var(--transition), box-shadow var(--transition); box-shadow: 0 4px 12px var(--accent-dim); }
        .btn:hover { opacity: 0.94; transform: translateY(-2px); box-shadow: 0 6px 16px var(--accent-dim); }
        .btn:active { transform: translateY(0); }
        .btn-secondary { background: var(--surface2); color: var(--text); border: 1px solid var(--border); box-shadow: none; }
        .btn-secondary:hover { border-color: var(--accent); color: var(--accent); background: var(--surface); }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.72); z-index: 1000; }
        .modal-content { background: var(--surface); margin: 3rem auto; padding: 2rem; border-radius: calc(var(--radius) * 1.2); width: min(90%, 900px); max-height: 85vh; overflow-y: auto; box-shadow: var(--shadow); animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        @keyframes popIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        .close { float: right; font-size: 1.8rem; cursor: pointer; color: var(--text-muted); }
        .form-group { margin-bottom: 1.25rem; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: var(--text); }
        input, textarea, select { width: 100%; padding: 0.85rem 1rem; border-radius: calc(var(--radius) - 2px); border: 1px solid var(--border); background: var(--surface2); color: var(--text); outline: none; transition: border-color var(--transition); }
        input:focus, textarea:focus, select:focus { border-color: var(--accent); }
        textarea { min-height: 280px; font-family: inherit; }
        .actions { margin-top: 2rem; display: flex; gap: 1rem; justify-content: flex-end; flex-wrap: wrap; }
        .editor-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1.5rem; }
        .editor-path { color: var(--text-muted); font-size: 0.95rem; margin-top: 0.35rem; word-break: break-word; }
        .editor-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; }
        .metadata-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-bottom: 1rem; }
        .meta-card { background: var(--surface2); border: 1px solid var(--border); border-radius: 14px; padding: 1rem; transition: transform var(--transition), border-color var(--transition); }
        .meta-card:hover { transform: translateY(-2px); border-color: var(--accent); }
        .meta-card strong { display: block; margin-bottom: 0.35rem; color: var(--text-muted); }
        .preview-tabs { display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
        .preview-panel, .metadata-panel, .raw-panel { display: none; }
        .panel-visible { display: block; animation: fadeIn 0.3s ease-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        .preview-frame { width: 100%; min-height: 520px; border: 1px solid var(--border); border-radius: 14px; background: #000; }
        .code-editor { font-family: 'JetBrains Mono', Consolas, monospace; font-size: 0.95rem; line-height: 1.5; white-space: pre-wrap; resize: vertical; }
        .file-tree { list-style: none; padding-left: 0; }
        .file-tree li { margin: 0.25rem 0; position: relative; }
        .file-tree ul { list-style: none; padding-left: 1.25rem; margin-top: 0.25rem; border-left: 1px solid var(--border); margin-left: 0.75rem; }
        .file-tree .folder, .file-tree .file { display: inline-flex; align-items: center; gap: 0.6rem; padding: 0.5rem 0.85rem; border-radius: 8px; transition: all var(--transition); width: 100%; user-select: none; }
        .file-tree .folder:hover, .file-tree .file:hover { background: var(--surface2); transform: translateX(3px); color: var(--text); }
        .file-tree .folder { font-weight: 700; color: var(--accent); }
        .file-tree .file { color: var(--text); font-size: 0.95rem; }
        .topbar { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1rem 1.5rem; background: var(--surface); border-bottom: 1px solid var(--border); margin-bottom: 1rem; border-radius: 0 0 var(--radius) var(--radius); }
        .topbar-title { font-family: 'Playfair Display', serif; font-size: 1.35rem; font-weight: 700; letter-spacing: 0.02em; }
        .topbar-actions { display: flex; flex-wrap: wrap; gap: 0.75rem; }
        .tab-button { padding: 0.65rem 1.2rem; border-radius: 999px; border: 1px solid var(--border); background: var(--surface2); color: var(--text); cursor: pointer; transition: background var(--transition), border-color var(--transition), color var(--transition), transform var(--transition); font-weight: 600; }
        .tab-button:hover { border-color: var(--accent); transform: translateY(-1px); }
        .tab-button.active { background: var(--accent); color: #000; border-color: transparent; transform: none; }
        .editor-panel { display: none; }
        .editor-panel.panel-visible { display: block; }
        .question-card { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; margin-bottom: 1rem; }
        .question-card .question-header { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 1rem; }
        .question-card .question-index { font-weight: 700; color: var(--accent); }
        .question-card .remove-question { background: transparent; border: 1px solid var(--wrong); color: var(--wrong); border-radius: 10px; padding: 0.45rem 0.75rem; cursor: pointer; font-weight: 600; }
        .question-card .remove-question:hover { background: var(--wrong); color: #fff; }
        .editor-field { margin-bottom: 1rem; }
        .editor-field label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: var(--text); }
        .editor-field input, .editor-field textarea { width: 100%; padding: 0.75rem; border-radius: var(--radius); border: 1px solid var(--border); background: var(--surface2); color: var(--text); font-family: inherit; }
        .editor-option-row { display: flex; gap: 0.6rem; align-items: center; margin-bottom: 0.5rem; }
        .editor-options-list { display: flex; flex-direction: column; gap: 0; }
        .editor-option-row .option-radio { width: 18px; height: 18px; cursor: pointer; accent-color: var(--correct); flex-shrink: 0; }
        .editor-option { flex: 1; }
    </style>
</head>
<body>
    <div class="topbar">
        <div class="topbar-title">Admin Dashboard</div>
        <div class="topbar-actions">
            <button class="btn btn-secondary" onclick="refreshTree()">Refresh</button>
            <button class="btn btn-secondary" onclick="showModal('new-folder')">New Folder</button>
            <button class="btn btn-secondary" onclick="showModal('new-file')">New File</button>
            <button class="btn btn-secondary" onclick="showModal('git-actions')">Git Actions</button>
            <button class="btn btn-secondary" id="theme-toggle" onclick="toggleTheme()" title="Toggle theme" style="width: 44px; padding: 0; display: inline-flex; align-items: center; justify-content: center;">☀</button>
        </div>
    </div>
    <div class="container">
        <header class="header">
            <h1>Admin Dashboard - <span>{{ project_name }}</span></h1>
            <p>Browse quizzes, edit HTML, and manage Git from one local interface.</p>
        </header>

        <div class="main-grid">
            <aside class="sidebar">
                <h3>File Tree</h3>
                <ul class="file-tree" id="file-tree"></ul>
                <div class="actions">
                    <button class="btn" onclick="showModal('new-folder')">New Folder</button>
                    <button class="btn" onclick="showModal('new-file')">New File</button>
                </div>
            </aside>

            <main class="content">
                <div id="content-area">
                    <p>Select a file from the tree to edit, or use the buttons to create new content.</p>
                </div>
            </main>
        </div>
    </div>

    <!-- Modals -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div id="modal-body"></div>
        </div>
    </div>

    <script>
        let currentFile = null;
        let currentFileData = null;
        let fileTree = {};

        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('admin-theme', newTheme);
            document.getElementById('theme-toggle').textContent = newTheme === 'light' ? '🌙' : '☀';
        }
        (function() {
            var savedTheme = localStorage.getItem('admin-theme') || 'dark';
            document.documentElement.setAttribute('data-theme', savedTheme);
            window.addEventListener('DOMContentLoaded', () => {
                const btn = document.getElementById('theme-toggle');
                if(btn) btn.textContent = savedTheme === 'light' ? '🌙' : '☀';
            });
        })();

        function updateMetadataPanel(meta) {
            return `
                <div class="metadata-grid">
                    <div class="meta-card"><strong>Type</strong><span>${meta.type || 'html'}</span></div>
                    <div class="meta-card"><strong>UID</strong><span>${meta.uid || '—'}</span></div>
                    <div class="meta-card"><strong>Title</strong><span>${escapeHtml(meta.title || '—')}</span></div>
                    <div class="meta-card"><strong>Description</strong><span>${escapeHtml(meta.description || '—')}</span></div>
                    ${meta.type === 'index' ? `<div class="meta-card"><strong>Hero Title</strong><span>${escapeHtml(meta.hero_title || '—')}</span></div>` : ''}
                    <div class="meta-card"><strong>Questions</strong><span>${meta.question_count != null ? meta.question_count : '—'}</span></div>
                    <div class="meta-card"><strong>Icon</strong><span>${escapeHtml(meta.icon || '—')}</span></div>
                </div>
            `;
        }

        async function loadFileTree() {
            const response = await fetch('/admin/files');
            fileTree = await response.json();
            renderFileTree(fileTree, document.getElementById('file-tree'));
        }

        function renderFileTree(tree, container, parentPath = '') {
            container.innerHTML = '';
            for (const [name, item] of Object.entries(tree)) {
                const li = document.createElement('li');
                if (item.type === 'folder') {
                    const path = item.path || (parentPath ? `${parentPath}/${name}` : name);
                    const id = `folder-${path.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
                    const safeName = escapeHtml(name).replace(/'/g, "\\'");
                    li.innerHTML = `<span class="folder" id="lbl-${id}" onclick="toggleFolder('${id}', '${safeName}')"><span class="folder-icon">📁</span> ${escapeHtml(name)}</span>`;
                    const subUl = document.createElement('ul');
                    subUl.id = id;
                    subUl.style.display = 'none';
                    renderFileTree(item.children, subUl, path);
                    li.appendChild(subUl);
                } else {
                    li.innerHTML = `<span class="file" onclick="loadFile('${encodeURIComponent(item.path)}')">${item.icon || '📄'} ${escapeHtml(name)}</span>`;
                }
                container.appendChild(li);
            }
        }

        function toggleFolder(id, name) {
            const ul = document.getElementById(id);
            const lbl = document.getElementById(`lbl-${id}`);
            if (!ul) return;
            if (ul.style.display === 'none') {
                ul.style.display = 'block';
                if(lbl) lbl.innerHTML = `<span class="folder-icon">📂</span> ${name}`;
            } else {
                ul.style.display = 'none';
                if(lbl) lbl.innerHTML = `<span class="folder-icon">📁</span> ${name}`;
            }
        }

        async function loadFile(path) {
            currentFile = decodeURIComponent(path);
            const response = await fetch(`/admin/load-file?path=${encodeURIComponent(currentFile)}`);
            const data = await response.json();
            const meta = data.meta || {};
            const previewPath = `/preview/${encodeURIComponent(currentFile)}`;
            currentFileData = { content: data.content, meta };
            const editorTabVisible = ['quiz', 'bank', 'index'].includes(meta.type);
            document.getElementById('content-area').innerHTML = `
                <div class="editor-header">
                    <div>
                        <h3>Editing</h3>
                        <p class="editor-path">${currentFile}</p>
                    </div>
                    <div class="editor-actions">
                        <button class="btn btn-secondary" onclick="showModal('move-file')">Move</button>
                        <button class="btn btn-secondary" onclick="convertFile()">Convert</button>
                        <button class="btn btn-secondary" onclick="window.open('${previewPath}', '_blank')">Open Preview</button>
                        <button class="btn" onclick="saveFile()" id="save-button">Save</button>
                    </div>
                </div>
                <div class="metadata-grid">
                    <div class="meta-card"><strong>Type</strong><span>${meta.type || 'html'}</span></div>
                    <div class="meta-card"><strong>UID</strong><span>${meta.uid || '—'}</span></div>
                    <div class="meta-card"><strong>Title</strong><span>${escapeHtml(meta.title || '—')}</span></div>
                    <div class="meta-card"><strong>Description</strong><span>${escapeHtml(meta.description || '—')}</span></div>
                    <div class="meta-card"><strong>Questions</strong><span>${meta.question_count != null ? meta.question_count : '—'}</span></div>
                    <div class="meta-card"><strong>Icon</strong><span>${escapeHtml(meta.icon || '—')}</span></div>
                </div>
                <div class="preview-tabs">
                    <button class="tab-button active" data-tab="preview" onclick="setPreviewTab('preview')">Preview</button>
                    <button class="tab-button" data-tab="editor" id="editor-tab-button" style="display: ${editorTabVisible ? 'inline-flex' : 'none'}" onclick="setPreviewTab('editor')">Editor</button>
                    <button class="tab-button" data-tab="metadata" onclick="setPreviewTab('metadata')">Metadata</button>
                    <button class="tab-button" data-tab="raw" onclick="setPreviewTab('raw')">Raw HTML</button>
                </div>
                <div id="preview-panel" class="preview-panel panel-visible">
                    <iframe class="preview-frame" src="${previewPath}" title="Preview of ${currentFile}"></iframe>
                </div>
                <div id="editor-panel" class="editor-panel"></div>
                <div id="metadata-panel" class="metadata-panel">
                    <div class="form-group"><label>Parsed Metadata</label><textarea readonly class="code-editor" rows="12">${escapeHtml(JSON.stringify(meta, null, 2))}</textarea></div>
                </div>
                <div id="raw-panel" class="raw-panel">
                    <div class="form-group">
                        <label>Raw HTML</label>
                        <textarea id="file-content" class="code-editor" rows="24">${escapeHtml(data.content)}</textarea>
                    </div>
                </div>
            `;
            updateEditorButtons();
            if (editorTabVisible) renderEditorPanel();
            document.getElementById('file-content').addEventListener('input', () => {
                document.getElementById('save-button').textContent = 'Save*';
            });
        }

        function setPreviewTab(tab) {
            document.querySelectorAll('.preview-tabs button').forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tab));
            document.getElementById('preview-panel').classList.toggle('panel-visible', tab === 'preview');
            document.getElementById('editor-panel').classList.toggle('panel-visible', tab === 'editor');
            document.getElementById('metadata-panel').classList.toggle('panel-visible', tab === 'metadata');
            document.getElementById('raw-panel').classList.toggle('panel-visible', tab === 'raw');
            if (tab === 'editor') {
                renderEditorPanel();
            }
        }

        function updateEditorButtons() {
            const editorTab = document.getElementById('editor-tab-button');
            if (!editorTab) return;
            const showEditor = currentFileData && ['quiz', 'bank', 'index'].includes(currentFileData.meta.type);
            editorTab.style.display = showEditor ? 'inline-flex' : 'none';
        }

        function renderEditorPanel() {
            const panel = document.getElementById('editor-panel');
            if (!panel || !currentFileData) {
                return;
            }
            const meta = currentFileData.meta;
            if (meta.type === 'quiz' || meta.type === 'bank') {
                renderQuizBankEditor(panel, meta);
            } else if (meta.type === 'index') {
                renderIndexEditor(panel, meta);
            } else {
                panel.innerHTML = '<p>Structured editing not available for this file type.</p>';
            }
        }

        function renderQuizBankEditor(panel, meta) {
            const questions = meta.questions || [];
            const isBank = meta.type === 'bank';
            panel.innerHTML = `
                <div class="editor-field">
                    <label>UID</label>
                    <input type="text" id="editor-uid" value="${escapeHtml(meta.config?.uid || '')}" oninput="syncEditorData()">
                </div>
                <div class="editor-field">
                    <label>Title</label>
                    <input type="text" id="editor-title" value="${escapeHtml(meta.config?.title || '')}" oninput="syncEditorData()">
                </div>
                <div class="editor-field">
                    <label>Description</label>
                    <textarea id="editor-description" rows="3" oninput="syncEditorData()">${escapeHtml(meta.config?.description || '')}</textarea>
                </div>
                ${isBank ? `
                    <div class="editor-field">
                        <label>Icon</label>
                        <input type="text" id="editor-icon" value="${escapeHtml(meta.config?.icon || '🗃️')}" oninput="syncEditorData()">
                    </div>
                ` : ''}
                <div id="questions-list"></div>
                <button class="btn btn-secondary" style="width:100%;margin-top:1rem;" onclick="addEditorQuestion()">+ Add Question</button>
            `;
            const questionsList = document.getElementById('questions-list');
            questionsList.innerHTML = '';
            questions.forEach((question, index) => {
                const card = document.createElement('div');
                card.className = 'question-card';
                card.innerHTML = `
                    <div class="question-header">
                        <span class="question-index">Question ${index + 1}</span>
                        <button class="remove-question" type="button" onclick="removeEditorQuestion(${index})">Remove</button>
                    </div>
                    <div class="editor-field">
                        <label>Question</label>
                        <textarea class="editor-question" rows="3" oninput="syncEditorData()">${escapeHtml(question.question || '')}</textarea>
                    </div>
                    <div class="editor-field">
                        <label>Options <span style="color:var(--text-muted);font-weight:400;font-size:0.8rem;">(● = correct answer)</span></label>
                        <div class="editor-options-list">
                        ${question.options.map((opt, optIndex) => `
                            <div class="editor-option-row">
                                <input type="radio" name="correct-${index}" class="option-radio" value="${optIndex}" ${question.correct === optIndex ? 'checked' : ''} onchange="syncEditorData()">
                                <input class="editor-option" type="text" value="${escapeHtml(opt || '')}" placeholder="Option ${String.fromCharCode(65 + optIndex)}" oninput="syncEditorData()">
                            </div>`).join('')}
                        </div>
                    </div>
                    <div class="editor-field">
                        <label>Explanation</label>
                        <textarea class="editor-explanation" rows="2" oninput="syncEditorData()">${escapeHtml(question.explanation || '')}</textarea>
                    </div>
                `;
                questionsList.appendChild(card);
            });
        }

        function renderIndexEditor(panel, meta) {
            const quizzes = meta.quizzes || [];
            panel.innerHTML = `
                <div class="editor-field">
                    <label>Page Title</label>
                    <input type="text" id="index-page-title" value="${escapeHtml(meta.title || '')}" oninput="syncEditorData()">
                </div>
                <div class="editor-field">
                    <label>Hero Title (HTML allowed)</label>
                    <input type="text" id="index-hero-title" value="${escapeHtml(meta.hero_title || '')}" oninput="syncEditorData()">
                </div>
                <div class="editor-field">
                    <label>Hero Description</label>
                    <textarea id="index-hero-desc" rows="2" oninput="syncEditorData()">${escapeHtml(meta.description || '')}</textarea>
                </div>
                <hr style="border:0;border-top:1px solid var(--border);margin:1.5rem 0;">
                <div class="editor-field">
                    <label>Index Cards</label>
                    <p class="hint" style="color:var(--text-muted);font-size:0.9rem;margin-bottom:1rem;">Edit card title, description, icon, tags, and URL. This updates the QUIZZES array in the index page.</p>
                </div>
                <div id="index-entries"></div>
                <button class="btn btn-secondary" style="width:100%;margin-top:1rem;" onclick="addIndexCard()">+ Add Card</button>
            `;
            const entries = document.getElementById('index-entries');
            entries.innerHTML = '';
            quizzes.forEach((quiz, index) => {
                const card = document.createElement('div');
                card.className = 'question-card';
                card.innerHTML = `
                    <div class="question-header">
                        <span class="question-index">Card ${index + 1}</span>
                        <button class="remove-question" type="button" onclick="removeIndexCard(${index})">Remove</button>
                    </div>
                    <div class="editor-field">
                        <label>Title</label>
                        <input class="index-title" type="text" value="${escapeHtml(quiz.title || '')}" oninput="syncEditorData()">
                    </div>
                    <div class="editor-field">
                        <label>Description</label>
                        <textarea class="index-description" rows="2" oninput="syncEditorData()">${escapeHtml(quiz.description || '')}</textarea>
                    </div>
                    <div class="editor-field">
                        <label>Icon</label>
                        <input class="index-icon" type="text" value="${escapeHtml(quiz.icon || '')}" oninput="syncEditorData()">
                    </div>
                    <div class="editor-field">
                        <label>URL</label>
                        <input class="index-url" type="text" value="${escapeHtml(quiz.url || '')}" oninput="syncEditorData()">
                    </div>
                    <div class="editor-field">
                        <label>Tags (comma separated)</label>
                        <input class="index-tags" type="text" value="${escapeHtml((quiz.tags || []).join(', '))}" oninput="syncEditorData()">
                    </div>
                `;
                entries.appendChild(card);
            });
        }

        function syncEditorData() {
            if (!currentFileData) return;
            const meta = currentFileData.meta;
            if (meta.type === 'quiz' || meta.type === 'bank') {
                const title = document.getElementById('editor-title')?.value || '';
                const description = document.getElementById('editor-description')?.value || '';
                const uid = document.getElementById('editor-uid')?.value || '';
                const icon = document.getElementById('editor-icon')?.value || '🗃️';
                const questions = Array.from(document.querySelectorAll('.question-card')).map(card => {
                    const questionText = card.querySelector('.editor-question')?.value || '';
                    const options = Array.from(card.querySelectorAll('.editor-option')).map(input => input.value || '');
                    const checkedRadio = card.querySelector('.option-radio:checked');
                    const correct = checkedRadio ? parseInt(checkedRadio.value, 10) : 0;
                    const explanation = card.querySelector('.editor-explanation')?.value || '';
                    return { question: questionText, options, correct, explanation };
                });
                meta.config = meta.config || {};
                meta.config.uid = uid;
                meta.config.title = title;
                meta.config.description = description;
                if (meta.type === 'bank') meta.config.icon = icon;
                meta.questions = questions;
                const currentHtml = document.getElementById('file-content')?.value || currentFileData.content;
                currentFileData.content = replaceQuizBankBlock(currentHtml, meta.type, meta.config, questions);
            } else if (meta.type === 'index') {
                const pageTitle = document.getElementById('index-page-title')?.value || '';
                const heroTitle = document.getElementById('index-hero-title')?.value || '';
                const heroDesc = document.getElementById('index-hero-desc')?.value || '';
                
                meta.title = pageTitle;
                meta.hero_title = heroTitle;
                meta.description = heroDesc;

                const quizzes = Array.from(document.querySelectorAll('#index-entries .question-card')).map(card => {
                    const title = card.querySelector('.index-title')?.value || '';
                    const description = card.querySelector('.index-description')?.value || '';
                    const icon = card.querySelector('.index-icon')?.value || '';
                    const url = card.querySelector('.index-url')?.value || '';
                    const tags = (card.querySelector('.index-tags')?.value || '').split(',').map(tag => tag.trim()).filter(Boolean);
                    const entry = { title, description, url };
                    if (icon) entry.icon = icon;
                    if (tags.length) entry.tags = tags;
                    return entry;
                });
                meta.quizzes = quizzes;
                
                let currentHtml = document.getElementById('file-content')?.value || currentFileData.content;
                currentHtml = replaceQuizzesBlock(currentHtml, quizzes);
                
                if (pageTitle) {
                    currentHtml = currentHtml.replace(/<title>[\s\S]*?<\/title>/i, `<title>${escapeHtml(pageTitle)}</title>`);
                    currentHtml = currentHtml.replace(/<div class="topbar-title">[\s\S]*?<\/div>/i, `<div class="topbar-title">${escapeHtml(pageTitle)}</div>`);
                }
                if (heroTitle || heroDesc) {
                    currentHtml = currentHtml.replace(/<header class="hero">\s*<h1>[\s\S]*?<\/h1>\s*<p>[\s\S]*?<\/p>\s*<\/header>/i, `<header class="hero">\n      <h1>${heroTitle}</h1>\n      <p>${escapeHtml(heroDesc)}</p>\n    </header>`);
                }
                
                currentFileData.content = currentHtml;
            }
            const rawArea = document.getElementById('file-content');
            if (rawArea) {
                rawArea.value = currentFileData.content;
            }
            updateMetadataDisplay();
            const saveButton = document.getElementById('save-button');
            if (saveButton) saveButton.textContent = 'Save*';
        }

        function replaceConfigBlock(html, blockName, configObj) {
            const configJson = JSON.stringify(configObj, null, 2);
            const startMatch = html.match(new RegExp('const\\s+' + blockName + '\\s*=\\s*\\{'));
            if (startMatch) {
                const startIdx = html.indexOf(startMatch[0]);
                const blockStart = startIdx + startMatch[0].length - 1;
                let braceCount = 0;
                let blockEnd = -1;
                for (let i = blockStart; i < html.length; i++) {
                    if (html[i] === '{') braceCount++;
                    else if (html[i] === '}') {
                        braceCount--;
                        if (braceCount === 0) {
                            blockEnd = i;
                            break;
                        }
                    }
                }
                if (blockEnd !== -1) {
                    const before = html.substring(0, startIdx);
                    const after = html.substring(blockEnd + 1);
                    return before + 'const ' + blockName + ' = ' + configJson + after;
                }
            }
            return html;
        }

        function replaceArrayBlock(html, arrayName, arrayObj) {
            const arrayJson = JSON.stringify(arrayObj, null, 2);
            const startMatch = html.match(new RegExp('const\\s+' + arrayName + '\\s*=\\s*\\['));
            if (startMatch) {
                const startIdx = html.indexOf(startMatch[0]);
                const blockStart = startIdx + startMatch[0].length - 1;
                let bracketCount = 0;
                let blockEnd = -1;
                for (let i = blockStart; i < html.length; i++) {
                    if (html[i] === '[') bracketCount++;
                    else if (html[i] === ']') {
                        bracketCount--;
                        if (bracketCount === 0) {
                            blockEnd = i;
                            break;
                        }
                    }
                }
                if (blockEnd !== -1) {
                    const before = html.substring(0, startIdx);
                    const after = html.substring(blockEnd + 1);
                    return before + 'const ' + arrayName + ' = ' + arrayJson + after;
                }
            }
            return html;
        }

        function replaceQuizBankBlock(html, type, config, questions) {
            let result = html;
            const blockName = type === 'bank' ? 'BANK_CONFIG' : 'QUIZ_CONFIG';
            const arrayName = type === 'bank' ? 'QUESTION_BANK' : 'QUESTIONS';
            result = replaceConfigBlock(result, blockName, config);
            result = replaceArrayBlock(result, arrayName, questions);
            return result;
        }

        function replaceQuizzesBlock(html, quizzes) {
            return replaceArrayBlock(html, 'QUIZZES', quizzes);
        }

        function addEditorQuestion() {
            if (!currentFileData) return;
            currentFileData.meta.questions = currentFileData.meta.questions || [];
            currentFileData.meta.questions.push({ question: '', options: ['', '', '', ''], correct: 0, explanation: '' });
            renderEditorPanel();
            syncEditorData();
        }

        function removeEditorQuestion(index) {
            if (!currentFileData) return;
            currentFileData.meta.questions.splice(index, 1);
            renderEditorPanel();
            syncEditorData();
        }

        function addIndexCard() {
            if (!currentFileData) return;
            currentFileData.meta.quizzes = currentFileData.meta.quizzes || [];
            currentFileData.meta.quizzes.push({ title: '', description: '', url: '', icon: '', tags: [] });
            renderEditorPanel();
            syncEditorData();
        }

        function removeIndexCard(index) {
            if (!currentFileData) return;
            currentFileData.meta.quizzes.splice(index, 1);
            renderEditorPanel();
            syncEditorData();
        }

        function updateMetadataDisplay() {
            const metaText = document.querySelector('#metadata-panel textarea');
            if (metaText && currentFileData) {
                metaText.value = JSON.stringify(currentFileData.meta, null, 2);
            }
        }

        async function saveFile() {
            const contentField = document.getElementById('file-content');
            if (!contentField) {
                alert('No file is loaded.');
                return;
            }
            const content = contentField.value;
            const response = await fetch('/admin/save-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: currentFile, content })
            });
            const result = await response.json();
            alert(result.message);
            if (response.ok) {
                runSync();
            }
        }

        async function convertFile() {
            const response = await fetch('/admin/convert-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: currentFile })
            });
            const result = await response.json();
            alert(result.message);
            if (response.ok) {
                loadFile(currentFile); // Reload
                runSync();
            }
        }

        async function runSync() {
            await fetch('/admin/run-sync', { method: 'POST' });
            refreshTree();
        }

        function refreshTree() {
            loadFileTree();
        }

        function showModal(type) {
            let body = '';
            if (type === 'new-folder') {
        
                body = `
                    <h3>Create New Folder</h3>
                    <div class="form-group">
                        <label>Folder Name:</label>
                        <input type="text" id="new-folder-name" placeholder="e.g. gyn/new-topic">
                    </div>
                    <div class="actions">
                        <button class="btn" onclick="createFolder()">Create</button>
                    </div>
                `;
            } else if (type === 'new-file') {
                body = `
                    <h3>Create New File</h3>
                    <div class="form-group">
                        <label>Type:</label>
                        <select id="new-file-type">
                            <option value="quiz">Quiz</option>
                            <option value="bank">Question Bank</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Title:</label>
                        <input type="text" id="new-file-title" placeholder="L1 Anatomy">
                    </div>
                    <div class="form-group">
                        <label>Description:</label>
                        <input type="text" id="new-file-desc" placeholder="Short description">
                    </div>
                    <div class="form-group">
                        <label>Folder:</label>
                        <select id="new-file-folder"></select>
                    </div>
                    <div class="actions">
                        <button class="btn" onclick="createFile()">Create</button>
                    </div>
                `;
                setTimeout(populateFolderDropdown, 0);
            } else if (type === 'move-file') {
                body = `
                    <h3>Move File</h3>
                    <div class="form-group">
                        <label>Target Folder:</label>
                        <select id="move-file-folder"></select>
                    </div>
                    <div class="actions">
                        <button class="btn" onclick="moveFile()">Move</button>
                    </div>
                `;
                setTimeout(populateFolderDropdown, 0);
            } else if (type === 'git-actions') {
                body = `
                    <h3>Git Actions</h3>
                    <div class="form-group">
                        <label>Commit Message:</label>
                        <input type="text" id="commit-message" value="Update quiz files">
                    </div>
                    <div class="actions">
                        <button class="btn" onclick="commitChanges()">Commit</button>
                        <button class="btn btn-secondary" onclick="pushChanges()">Push</button>
                    </div>
                `;
            }
            document.getElementById('modal-body').innerHTML = body;
            document.getElementById('modal').style.display = 'block';
        }

        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }

        async function createFolder() {
            const name = document.getElementById('new-folder-name').value;
            const response = await fetch('/admin/create-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const result = await response.json();
            alert(result.message);
            if (response.ok) {
                closeModal();
                refreshTree();
                runSync();
            }
        }

        async function createFile() {
            const type = document.getElementById('new-file-type').value;
            const title = document.getElementById('new-file-title').value;
            const desc = document.getElementById('new-file-desc').value;
            const folder = document.getElementById('new-file-folder').value;
            const response = await fetch('/admin/create-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, title, description: desc, folder })
            });
            const result = await response.json();
            alert(result.message);
            if (response.ok) {
                closeModal();
                refreshTree();
                runSync();
            }
        }

        async function moveFile() {
            const folder = document.getElementById('move-file-folder').value;
            const response = await fetch('/admin/move-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: currentFile, folder })
            });
            const result = await response.json();
            alert(result.message);
            if (response.ok) {
                currentFile = result.path;
                closeModal();
                refreshTree();
                loadFile(currentFile);
            }
        }

        async function commitChanges() {
            const message = document.getElementById('commit-message').value;
            const response = await fetch('/admin/git-commit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            const result = await response.json();
            alert(result.message);
            if (response.ok) {
                closeModal();
            }
        }

        async function pushChanges() {
            const response = await fetch('/admin/git-push', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await response.json();
            alert(result.message);
            if (response.ok) {
                closeModal();
            }
        }

        async function populateFolderDropdown() {
            const response = await fetch('/admin/folders');
            if (!response.ok) return;
            const folders = await response.json();
            const createSelect = document.getElementById('new-file-folder');
            const moveSelect = document.getElementById('move-file-folder');
            if (createSelect) {
                createSelect.innerHTML = '';
                folders.forEach(folder => {
                    const opt = document.createElement('option');
                    opt.value = folder;
                    opt.textContent = folder === '.' ? 'root' : folder;
                    createSelect.appendChild(opt);
                });
            }
            if (moveSelect) {
                moveSelect.innerHTML = '';
                folders.forEach(folder => {
                    const opt = document.createElement('option');
                    opt.value = folder;
                    opt.textContent = folder === '.' ? 'root' : folder;
                    moveSelect.appendChild(opt);
                });
            }
        }

        function escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        // Load initial data
        loadFileTree();
    </script>
</body>
</html>
"""

# Utility functions
def get_project_name():
    """Get project name from manifest or directory"""
    manifest = PROJECT_ROOT / 'manifest.webmanifest'
    if manifest.exists():
        try:
            with open(manifest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('name', 'Quiz Project')
        except:
            pass
    return PROJECT_ROOT.name

def scan_files():
    """Scan for HTML files and build tree structure"""
    tree = {}
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip hidden dirs and scripts
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'scripts' and d != '__pycache__']

        rel_root = os.path.relpath(root, PROJECT_ROOT)
        parts = [] if rel_root == '.' else rel_root.split(os.sep)
        rel_parts = []
        current = tree
        for part in parts:
            rel_parts.append(part)
            current_rel_path = os.path.join(*rel_parts)
            if part not in current:
                current[part] = {'type': 'folder', 'path': os.path.normpath(current_rel_path), 'children': {}}
            current = current[part]['children']

        for file in files:
            if file.endswith('.html'):
                path = os.path.normpath(os.path.join(rel_root, file)) if rel_root != '.' else file
                icon = '📄'
                if file == 'index.html':
                    icon = '🏠'
                elif file.lower().startswith('all-') or file.lower().endswith('-bank.html'):
                    icon = '🗃️'
                current[file] = {'type': 'file', 'path': path, 'icon': icon}

    return tree


def scan_folders():
    """Return a list of folder paths for dropdowns"""
    folders = ['.']
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'scripts' and d != '__pycache__']
        rel_root = os.path.relpath(root, PROJECT_ROOT)
        if rel_root != '.':
            folders.append(rel_root)
    return sorted(set(folders))

def extract_block(content, prefix, open_char, close_char):
    import re
    match = re.search(rf'const\s+{prefix}\s*=\s*\{open_char}', content)
    if not match:
        return None
    start_idx = match.start()
    block_start = content.find(open_char, start_idx)
    if block_start == -1:
        return None
    brace_count = 0
    for i in range(block_start, len(content)):
        if content[i] == open_char:
            brace_count += 1
        elif content[i] == close_char:
            brace_count -= 1
            if brace_count == 0:
                return content[block_start:i+1]
    return None

def sanitize_json(block):
    import re
    block = re.sub(r'(?<!:)\/\/.*', '', block)
    block = re.sub(r'/\*.*?\*/', '', block, flags=re.DOTALL)
    block = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', block)
    block = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", lambda m: '"' + m.group(1).replace('"', '\\"') + '"', block)
    block = re.sub(r',\s*([\]}])', r'\1', block)
    return block

def parse_quiz_file(content):
    """Extract QUIZ_CONFIG or BANK_CONFIG from HTML"""
    block = extract_block(content, 'QUIZ_CONFIG', '{', '}')
    if block:
        try:
            return 'QUIZ_CONFIG', json.loads(block)
        except:
            try:
                return 'QUIZ_CONFIG', json.loads(sanitize_json(block))
            except:
                pass
    block = extract_block(content, 'BANK_CONFIG', '{', '}')
    if block:
        try:
            return 'BANK_CONFIG', json.loads(block)
        except:
            try:
                return 'BANK_CONFIG', json.loads(sanitize_json(block))
            except:
                pass
    return None, None

def parse_question_array(content, array_name):
    block = extract_block(content, array_name, '[', ']')
    if block:
        try:
            return json.loads(block)
        except:
            try:
                return json.loads(sanitize_json(block))
            except:
                pass
    return []

def parse_index_array(content):
    block = extract_block(content, 'QUIZZES', '[', ']')
    if block:
        try:
            return json.loads(block)
        except:
            try:
                return json.loads(sanitize_json(block))
            except:
                pass
    return None


def parse_file_metadata(content):
    config_type, config = parse_quiz_file(content)
    if config_type == 'QUIZ_CONFIG':
        questions = parse_question_array(content, 'QUESTIONS')
        return {
            'type': 'quiz',
            'uid': config.get('uid'),
            'title': config.get('title'),
            'description': config.get('description'),
            'question_count': len(questions),
            'config': config,
            'questions': questions
        }

    if config_type == 'BANK_CONFIG':
        bank_questions = parse_question_array(content, 'QUESTION_BANK')
        return {
            'type': 'bank',
            'uid': config.get('uid'),
            'title': config.get('title'),
            'description': config.get('description'),
            'icon': config.get('icon'),
            'question_count': len(bank_questions),
            'config': config,
            'questions': bank_questions
        }

    quizzes = parse_index_array(content)
    if quizzes is not None:
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        desc_match = re.search(r'<header class="hero">\s*<h1>(.*?)</h1>\s*<p>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)
        
        title = title_match.group(1).strip() if title_match else None
        hero_title = desc_match.group(1).strip() if desc_match else None
        hero_description = desc_match.group(2).strip() if desc_match else None

        return {
            'type': 'index',
            'title': title,
            'description': hero_description,
            'hero_title': hero_title,
            'question_count': len(quizzes),
            'quizzes': quizzes
        }

    return {'type': 'html', 'question_count': 0}


def generate_uid(prefix='file'):
    """Generate unique ID"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def create_quiz_html(config, questions=None):
    """Generate HTML for quiz file"""
    if questions is None:
        questions = [{"question": "Sample question?", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "Sample explanation."}]

    config_json = json.dumps(config, indent=2)
    questions_json = json.dumps(questions, indent=2)

    html = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>
(function(){{var t=localStorage.getItem('quiz-theme')||'dark';var s=document.createElement('style');
s.textContent='html,body{{background:'+(t==='light'?'#f3f0eb':'#0d1117')+';color:'+(t==='light'?'#1c1917':'#e6edf3')+';margin:0;padding:0;overflow:hidden;height:100%}}';
document.head.appendChild(s);}})();
</script>
<title>{config['title']}</title>
</head>
<body>
<script>
/* [QUIZ_CONFIG_START] */
const QUIZ_CONFIG = {config_json};
/* [QUIZ_CONFIG_END] */

/* [QUESTIONS_START] */
const QUESTIONS = {questions_json};
/* [QUESTIONS_END] */
</script>
<script>
(function(){{window.__QUIZ_ENGINE_BASE='../'.repeat(Math.max(0,location.pathname.split('/').filter(Boolean).length-2));
document.write('<scr'+'ipt src="'+window.__QUIZ_ENGINE_BASE+'quiz-engine.js"></scr'+'ipt>');}})();
</script>
</body>
</html>'''
    return html

def create_bank_html(config, questions=None):
    """Generate HTML for bank file"""
    if questions is None:
        questions = [{"question": "Sample question?", "options": ["A", "B", "C", "D"], "correct": 0, "explanation": "Sample explanation."}]

    config_json = json.dumps(config, indent=2)
    questions_json = json.dumps(questions, indent=2)

    html = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>
(function(){{var t=localStorage.getItem('quiz-theme')||'dark';var s=document.createElement('style');
s.textContent='html,body{{background:'+(t==='light'?'#f3f0eb':'#0d1117')+';color:'+(t==='light'?'#1c1917':'#e6edf3')+';margin:0;padding:0;overflow:hidden;height:100%}}';
document.head.appendChild(s);}})();
</script>
<title>{config['title']}</title>
</head>
<body>
<script>
/* [BANK_CONFIG_START] */
const BANK_CONFIG = {config_json};
/* [BANK_CONFIG_END] */

/* [QUESTION_BANK_START] */
const QUESTION_BANK = {questions_json};
/* [QUESTION_BANK_END] */
</script>
<script>
(function(){{window.__QUIZ_ENGINE_BASE='../'.repeat(Math.max(0,location.pathname.split('/').filter(Boolean).length-2));
document.write('<scr'+'ipt src="'+window.__QUIZ_ENGINE_BASE+'bank-engine.js"></scr'+'ipt>');}})();
</script>
</body>
</html>'''
    return html

# Flask Routes
@app.route('/')
def index():
    """Serve the main quiz site"""
    return send_from_directory(PROJECT_ROOT, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(PROJECT_ROOT, filename)

@app.route('/admin/')
def admin():
    """Serve admin dashboard"""
    project_name = get_project_name()
    return render_template_string(DASHBOARD_HTML, project_name=project_name)

@app.route('/admin/files')
def get_files():
    """Get file tree as JSON"""
    tree = scan_files()
    return jsonify(tree)

@app.route('/admin/folders')
def get_folders():
    """Get folder list as JSON"""
    folders = scan_folders()
    return jsonify(folders)

@app.route('/admin/load-file')
def load_file():
    """Load file content"""
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'No path provided'}), 400

    file_path = PROJECT_ROOT / path
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        meta = parse_file_metadata(content)
        return jsonify({'content': content, 'meta': meta})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview/<path:filename>')
def preview_file(filename):
    file_path = PROJECT_ROOT / filename
    if not file_path.exists() or not file_path.is_file():
        return 'Not Found', 404

    if file_path.suffix.lower() == '.html':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Adjust preview path logic so engine loader calculates base correctly.
            # Handle both GitHub Pages (with repo name) and local server (no repo name)
            content = re.sub(
                r"window\.__QUIZ_ENGINE_BASE\s*=\s*'\.\./'\.repeat\(Math\.max\(0,location\.pathname\.split\('/'\)\.filter\(Boolean\)\.length\s*-\s*2\)\);",
                "// Admin-Dashboard Preview Adjustment\nwindow.__QUIZ_ENGINE_BASE = '../'.repeat(Math.max(0, location.pathname.replace(/^\\/preview/, '').split('/').filter(Boolean).length - 1));",
                content
            )
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        except Exception as e:
            return f'Error loading preview: {e}', 500

    return send_from_directory(PROJECT_ROOT, filename)

@app.route('/admin/save-file', methods=['POST'])
def save_file():
    """Save file content"""
    data = request.get_json()
    path = data.get('path')
    content = data.get('content')

    if not path or content is None:
        return jsonify({'message': 'Missing path or content'}), 400

    file_path = PROJECT_ROOT / path
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'message': 'File saved successfully'})
    except Exception as e:
        return jsonify({'message': f'Error saving file: {str(e)}'}), 500

@app.route('/admin/create-folder', methods=['POST'])
def create_folder():
    """Create new folder with index.html"""
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'message': 'Missing folder name'}), 400

    folder_path = PROJECT_ROOT / name
    if folder_path.exists():
        return jsonify({'message': 'Folder already exists'}), 400

    try:
        folder_path.mkdir(parents=True)
        index_path = folder_path / 'index.html'

        depth = len(Path(name).parts)
        engine_path = '../' * depth + 'index-engine.js'
        index_html = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name}</title>
</head>
<body>
<h1>{name}</h1>
<p>Select your {name} exam.</p>
<div class="quiz-grid" id="quiz-grid"></div>
<script>
const QUIZZES = [];
</script>
<script src="{engine_path}"></script>
</body>
</html>'''

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)

        return jsonify({'message': f'Folder "{name}" created successfully'})
    except Exception as e:
        return jsonify({'message': f'Error creating folder: {str(e)}'}), 500

@app.route('/admin/create-file', methods=['POST'])
def create_file():
    """Create new quiz or bank file"""
    data = request.get_json()
    file_type = data.get('type')
    title = data.get('title')
    description = data.get('description', '')
    folder = data.get('folder', '.')

    if not all([file_type, title]):
        return jsonify({'message': 'Missing required fields'}), 400

    uid = generate_uid(file_type)
    safe_name = title.lower().replace(' ', '-').replace('/', '-').replace('\\', '-')
    filename = f"{safe_name}.html"
    target_folder = PROJECT_ROOT / folder
    if not target_folder.exists():
        return jsonify({'message': 'Target folder does not exist'}), 400

    if file_type == 'quiz':
        config = {
            'uid': uid,
            'title': title,
            'description': description
        }
        html = create_quiz_html(config)
    elif file_type == 'bank':
        config = {
            'uid': uid,
            'title': title,
            'description': description,
            'icon': '🗃️'
        }
        html = create_bank_html(config)
    else:
        return jsonify({'message': 'Invalid file type'}), 400

    file_path = target_folder / filename
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return jsonify({'message': f'{file_type.title()} file "{filename}" created successfully', 'path': os.path.relpath(file_path, PROJECT_ROOT)})
    except Exception as e:
        return jsonify({'message': f'Error creating file: {str(e)}'},), 500

@app.route('/admin/move-file', methods=['POST'])
def move_file():
    """Move file to a new folder"""
    data = request.get_json()
    path = data.get('path')
    folder = data.get('folder')

    if not path or folder is None:
        return jsonify({'message': 'Missing path or folder'}), 400

    source = PROJECT_ROOT / path
    target_folder = PROJECT_ROOT / folder
    if not source.exists():
        return jsonify({'message': 'File not found'}), 404
    if not target_folder.exists() or not target_folder.is_dir():
        return jsonify({'message': 'Target folder not found'}), 404

    try:
        destination = target_folder / source.name
        shutil.move(str(source), str(destination))
        return jsonify({'message': f'Moved to {folder}', 'path': os.path.relpath(destination, PROJECT_ROOT)})
    except Exception as e:
        return jsonify({'message': f'Error moving file: {str(e)}'},), 500

@app.route('/admin/convert-file', methods=['POST'])
def convert_file():
    """Convert quiz to bank or vice versa"""
    data = request.get_json()
    path = data.get('path')

    if not path:
        return jsonify({'message': 'Missing file path'}), 400

    file_path = PROJECT_ROOT / path
    if not file_path.exists():
        return jsonify({'message': 'File not found'}), 404

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        config_type, config = parse_quiz_file(content)
        if not config:
            return jsonify({'message': 'Could not parse file config'}), 400

        if config_type == 'QUIZ_CONFIG':
            # Convert to bank
            questions_match = re.search(r'const\s+QUESTIONS\s*=\s*(\[.*?\]);', content, re.DOTALL)
            if questions_match:
                questions = json.loads(questions_match.group(1))
                bank_config = {
                    'uid': generate_uid('bank'),
                    'title': config['title'],
                    'description': config['description'],
                    'icon': '🗃️'
                }
                html = create_bank_html(bank_config, questions)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                return jsonify({'message': 'Converted quiz to question bank'})
        elif config_type == 'BANK_CONFIG':
            # Convert to quiz
            bank_match = re.search(r'const\s+QUESTION_BANK\s*=\s*(\[.*?\]);', content, re.DOTALL)
            if bank_match:
                questions = json.loads(bank_match.group(1))
                quiz_config = {
                    'uid': generate_uid('quiz'),
                    'title': config['title'],
                    'description': config['description']
                }
                html = create_quiz_html(quiz_config, questions)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                return jsonify({'message': 'Converted question bank to quiz'})

        return jsonify({'message': 'Conversion not supported for this file'}), 400
    except Exception as e:
        return jsonify({'message': f'Error converting file: {str(e)}'}), 500

@app.route('/admin/run-sync', methods=['POST'])
def run_sync():
    """Run the sync script to update indexes"""
    if SYNC_SCRIPT.exists():
        try:
            result = subprocess.run(['python', str(SYNC_SCRIPT)], cwd=PROJECT_ROOT, capture_output=True, text=True)
            return jsonify({'message': 'Sync completed', 'output': result.stdout})
        except Exception as e:
            return jsonify({'message': f'Sync failed: {str(e)}'}), 500
    else:
        return jsonify({'message': 'Sync script not found'}), 404

@app.route('/admin/git-commit', methods=['POST'])
def git_commit():
    """Commit staged changes locally"""
    if not GIT_AVAILABLE:
        return jsonify({'message': 'GitPython not installed'}), 500

    data = request.get_json()
    message = data.get('message', 'Update quiz files')

    try:
        repo = git.Repo(PROJECT_ROOT)
        repo.git.add(A=True)
        repo.index.commit(message)
        return jsonify({'message': 'Changes committed successfully'})
    except Exception as e:
        return jsonify({'message': f'Git commit failed: {str(e)}'}), 500

@app.route('/admin/git-push', methods=['POST'])
def git_push():
    """Push committed changes to origin"""
    if not GIT_AVAILABLE:
        return jsonify({'message': 'GitPython not installed'}), 500

    try:
        repo = git.Repo(PROJECT_ROOT)
        origin = repo.remote('origin')
        origin.push()
        return jsonify({'message': 'Changes pushed successfully'})
    except Exception as e:
        return jsonify({'message': f'Git push failed: {str(e)}'}), 500

def open_browser():
    webbrowser.open('http://127.0.0.1:5500/admin/')

if __name__ == '__main__':
    print(f"Starting Admin Dashboard for {get_project_name()}")
    print("Opening http://localhost:5500/admin/ in your browser")
    print("Press Ctrl+C to stop")
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Timer(1.0, open_browser).start()
    app.run(host='127.0.0.1', port=5500, debug=True)