# Soulfra Flat Structure Map

**Generated:** Auto-analyzed from 18,843-line app.py

## Overview

- **Total routes:** 367
- **Imported modules:** 184
- **Active templates:** 138
- **Unused templates:** 52
- **Unused Python files:** 250

---

## Flask Routes (What app.py Actually Serves)

### API Routes (137)

- `GET` `/api-tester`
- `POST` `/api/ai-query`
- `GET` `/api/ai-stats`
- `POST` `/api/ai/clear-comments`
- `GET` `/api/ai/export-debug-data`
- `POST` `/api/ai/regenerate-all`
- `POST` `/api/ai/retrain-networks`
- `GET` `/api/ai/test-relevance/<int:post_id>`
- `GET` `/api/ai/training-data/<username>`
- `GET` `/api/assistant/history`
- `POST` `/api/assistant/message`
- `POST` `/api/assistant/post-comment`
- `POST` `/api/assistant/quick-actions`
- `POST` `/api/auto-deploy`
- `POST` `/api/brand-builder/chat`
- `POST` `/api/brand/consistency`
- `POST` `/api/brand/emoji/suggest`
- `POST` `/api/brand/generate`
- `POST` `/api/brand/predict`
- `GET` `/api/brand/status`
- ... and 117 more

### User/Profile Routes (14)

- `POST` `/api/assistant/message`
- `POST` `/api/discussion/message`
- `GET` `/api/membership/current`
- `POST` `/api/membership/upgrade`
- `POST` `/api/website/predict/method`
- `GET` `/me`
- `POST` `/me/delete`
- `GET` `/me/export`
- `GET` `/me/export-jsonld`
- `GET` `/me/quizzes`
- `GET` `/me/settings`
- `POST` `/me/settings/update`
- `GET` `/membership`
- `POST` `/practice/room/<room_id>/message`

### Admin/Debug Routes (55)

- `GET` `/admin`
- `GET` `/admin`
- `GET` `/admin/automation`
- `POST` `/admin/automation/bootstrap`
- `POST` `/admin/automation/generate-digest`
- `POST` `/admin/automation/publish-all`
- `POST` `/admin/automation/run-builder`
- `POST` `/admin/automation/run-syndication`
- `POST` `/admin/automation/send-digest`
- `POST` `/admin/automation/train-brand-models`
- `POST` `/admin/automation/train-website-model`
- `GET` `/admin/brand-status`
- `GET, POST` `/admin/brand/new`
- `GET, POST` `/admin/dashboard`
- `GET` `/admin/docs`
- `GET` `/admin/domains`
- `POST` `/admin/domains/add`
- `GET` `/admin/domains/analyze/<int:brand_id>`
- `GET` `/admin/domains/chat/<int:brand_id>`
- `POST` `/admin/domains/check-verification/<int:brand_id>`
- `POST` `/admin/domains/confirm-add`
- `GET` `/admin/domains/csv`
- `POST` `/admin/domains/delete/<int:brand_id>`
- `POST` `/admin/domains/edit/<int:brand_id>`
- `GET` `/admin/domains/import`
- `POST` `/admin/domains/import-csv`
- `POST` `/admin/domains/quick-add`
- `GET` `/admin/domains/relationships`
- `GET` `/admin/domains/verify/<int:brand_id>`
- `GET, POST` `/admin/form-builder`
- `GET` `/admin/freelancers`
- `GET, POST` `/admin/import-url`
- `GET` `/admin/join`
- `GET, POST` `/admin/login`
- `GET` `/admin/logout`
- `GET` `/admin/ollama`
- `GET, POST` `/admin/post/new`
- `GET` `/admin/set-session`
- `GET` `/admin/studio`
- `GET` `/admin/subscribers`
- `GET` `/admin/subscribers/export`
- `GET, POST` `/admin/subscribers/import`
- `GET` `/admin/token-usage`
- `GET` `/ai-network/debug`
- `GET` `/api/ai/export-debug-data`
- `GET` `/brand/<slug>/debug`
- `GET` `/debug`
- `GET` `/debug/map`
- `GET` `/debug/mirror/<brand>`
- `GET` `/debug/neural`
- `GET` `/debug/rotation`
- `POST` `/debug/sync-live`
- `GET` `/debug/system`
- `POST` `/debug/test-ai-comment`
- `GET` `/debug/theme`

---

## Active Templates (Actually Rendered)

### `admin/`

- domain_analysis.html
- domain_chat.html
- domain_preview.html
- domain_relationships.html
- domain_verify.html
- domains.html

### `catchphrase/`

- results_v1_dinghy.html
- test_v1_dinghy.html

### `challenge/`

- daily_v1_dinghy.html

### `cringeproof/`

- narrative.html
- play.html

### `debug/`

- neural_v1_dinghy.html
- theme_demo_v1_dinghy.html

### `idea_submission/`

- submit_form.html
- tracking.html

### `leaderboard/`

- v1_dinghy.html

### `learn/`

- dashboard.html
- review.html

### `me/`

- economy_dashboard.html
- quizzes.html
- settings.html

### `news_feed/`

- v1_dinghy.html

### `onboarding/`

- v1_dinghy.html

### `practice/`

- create.html
- index.html
- room.html

### `profile/`

- v1_dinghy.html

### `qr/`

- display.html

### `qr_question/`

- v1_dinghy.html

### `root/`

- about.html
- admin.html
- admin_automation.html
- admin_brand_new.html
- admin_form_builder.html
- admin_freelancers.html
- admin_import.html
- admin_import_url.html
- admin_login.html
- admin_master_portal.html
- admin_ollama.html
- admin_post_new.html
- admin_token_usage.html
- ai_network_debug.html
- ai_network_visualize.html
- ai_persona_detail.html
- api_docs.html
- api_tester.html
- brand_builder_chat.html
- brand_debug.html
- brand_page.html
- brand_preview.html
- brand_qr_stats.html
- brand_status.html
- brand_submission_result.html
- brand_submit.html
- brand_workspace.html
- brands_marketplace.html
- brands_overview.html
- category.html
- code_browser.html
- code_viewer.html
- content_generator.html
- content_manager.html
- csv_import.html
- dashboard.html
- debug_dashboard.html
- debug_system.html
- discussion_workspace.html
- docs.html
- domain_blog_index.html
- domain_blog_post.html
- domain_import.html
- domain_page.html
- domains_directory.html
- error.html
- factory.html
- features_dashboard.html
- feedback.html
- freelancer_signup_form.html
- freelancer_signup_success.html
- game_2plus2.html
- game_detail.html
- game_dnd.html
- games_gallery.html
- gated_search.html
- ghost_mode.html
- homebrew_lab.html
- hub.html
- join.html
- live.html
- login.html
- login_qr.html
- markdown_doc.html
- master_control_panel.html
- master_nav.html
- membership.html
- ml_dashboard.html
- my_domains.html
- ownership_dashboard.html
- playground.html
- post.html
- proof.html
- qr_search_gate.html
- quiz_complete.html
- reasoning.html
- search.html
- shipyard.html
- simple_test.html
- sitemap.html
- sitemap_game.html
- soul.html
- soul_platform_picker.html
- soul_similar.html
- soulfra_hub.html
- souls.html
- start.html
- status_dashboard.html
- studio.html
- subscribe.html
- tag.html
- template_browser.html
- trading.html
- train.html
- train_posts.html
- unified_dashboard.html
- unsubscribe.html
- user.html
- wiki_category.html
- wiki_concept.html
- wiki_index.html
- {template_filename}

### `signup/`

- v1_dinghy.html

### `start/`

- chapter.html
- journey.html

### `stpetepros/`

- homepage.html
- signup.html

### `user/`

- qr_card.html

### `widgets/`

- embed_preview.html

---

## Unused Templates (52)

These templates exist but are NEVER rendered by app.py:

### `admin/` - 1 files

- canvas_editor.html

### `components/` - 5 files

- footer.html
- header.html
- menu.html
- qr_display.html
- voice_recorder.html

### `cringeproof/` - 3 files

- leaderboard.html
- results.html
- room.html

### `games/` - 3 files

- analysis_results_v1_dinghy.html
- review_game_v1_dinghy.html
- share_button_v1_dinghy.html

### `generated/user_15/` - 2 files

- blog.html
- homepage.html

### `me/` - 1 files

- dashboard.html

### `qr/` - 2 files

- builder_v1_dinghy.html
- chat.html

### `root/` - 35 files

- admin_api_keys.html
- admin_brands.html
- admin_dashboard.html
- admin_deploy_ready.html
- admin_doc_view.html
- ... and 30 more

---

## Imported Modules (ACTIVE)

These Python files are imported by app.py:

- `affiliate_link_tracker.py`
- `aging_curves.py`
- `ai_host.py`
- `anki_learning_system.py`
- `api_routes.py`
- `automation_routes.py`
- `automation_workflows.py`
- `base64.py`
- `bidirectional_review_engine.py`
- `blamechain.py`
- `brand_ai_orchestrator.py`
- `brand_ai_persona_generator.py`
- `brand_builder.py`
- `brand_color_neural_network.py`
- `brand_config_validator.py`
- `brand_css_generator.py`
- `brand_neural_analysis.py`
- `brand_qr_generator.py`
- `brand_quality_gate.py`
- `brand_sop_templates.py`
- `brand_status_dashboard.py`
- `brand_theme_manager.py`
- `brand_vocabulary_trainer.py`
- `brand_voice_generator.py`
- `bs4.py`
- `build_routes.py`
- `business_routes.py`
- `canvas_routes.py`
- `chapter_tutorials.py`
- `chat_routes.py`
- `check_templates.py`
- `cleanup_orphaned_associations.py`
- `collections.py`
- `comment_github_integration.py`
- `comment_voice_chain.py`
- `concurrent.futures.py`
- `config.py`
- `content_transformer.py`
- `contribution_validator.py`
- `cringeproof.py`
- `cringeproof_personas.py`
- `cringeproof_reasoning.py`
- `csv.py`
- `database.py`
- `datetime.py`
- `db_helpers.py`
- `device_multiplier_system.py`
- `dm_via_qr.py`
- `dns.resolver.py`
- `docs_routes.py`
- ... and 134 more

---

## Unused Python Files (250)

These .py files exist but are NEVER imported:

- `PROOF_IT_ALL_WORKS.py`
- `SIMPLE_DEMO.py`
- `ad_injector.py`
- `admin_routes.py`
- `admin_system.py`
- `advanced_qr.py`
- `ai_image_generator.py`
- `analyze_app_structure.py`
- `analyze_dependencies.py`
- `api-debug-helper.py`
- `api_health_scanner.py`
- `api_image_generator.py`
- `api_server.py`
- `ascii_player.py`
- `audio_enhancer.py`
- `audio_quality.py`
- `audit_database.py`
- `audit_pii_exposure.py`
- `auto_content_generator.py`
- `auto_deploy_domain.py`
- `auto_fix_routes.py`
- `avatar_auto_attach.py`
- `avatar_generator.py`
- `backfill_mesh_network.py`
- `batch_import_posts.py`
- `battle_routes.py`
- `blog_syndication.py`
- `brand_creator.py`
- `build.py`
- `build_all.py`
- ... and 220 more

---

## Nested Soulfra Folder (SEPARATE PROJECT)

**Status:** NOT used by app.py (separate triple-domain system)

```
Soulfra/
├── Soulfra.com/    (QR landing - port 8001)
├── Soulfra.ai/     (AI chat - port 5003)
└── Soulfraapi.com/ (API - port 5002)
```

This is a SEPARATE mini-project with its own servers.
Main app.py runs on port 5001 - completely independent.

---

## VR/3D/Blender Features

**Status:** DOES NOT EXIST YET

No VR or 3D modeling code found.
Only 1 screenshot test in archive/experiments/.

**Future idea:** Reverse-engineer VR spatial interfaces into flat 2D screens
