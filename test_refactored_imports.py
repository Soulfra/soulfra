#!/usr/bin/env python3
"""
Test Refactored Imports - Verify nothing broke
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("🧪 Testing Refactored Imports")
print()

errors = []

# Test core imports
try:
    import core.PROOF_IT_ALL_WORKS
    print(f"✅ core.PROOF_IT_ALL_WORKS")
except Exception as e:
    print(f"❌ core.PROOF_IT_ALL_WORKS: {e}")
    errors.append("core.PROOF_IT_ALL_WORKS")

try:
    import core.SIMPLE_DEMO
    print(f"✅ core.SIMPLE_DEMO")
except Exception as e:
    print(f"❌ core.SIMPLE_DEMO: {e}")
    errors.append("core.SIMPLE_DEMO")

try:
    import core.app
    print(f"✅ core.app")
except Exception as e:
    print(f"❌ core.app: {e}")
    errors.append("core.app")

try:
    import core.app
    print(f"✅ core.app")
except Exception as e:
    print(f"❌ core.app: {e}")
    errors.append("core.app")

try:
    import core.app
    print(f"✅ core.app")
except Exception as e:
    print(f"❌ core.app: {e}")
    errors.append("core.app")

try:
    import core.ad_injector
    print(f"✅ core.ad_injector")
except Exception as e:
    print(f"❌ core.ad_injector: {e}")
    errors.append("core.ad_injector")

try:
    import core.admin_routes
    print(f"✅ core.admin_routes")
except Exception as e:
    print(f"❌ core.admin_routes: {e}")
    errors.append("core.admin_routes")

try:
    import core.admin_system
    print(f"✅ core.admin_system")
except Exception as e:
    print(f"❌ core.admin_system: {e}")
    errors.append("core.admin_system")

try:
    import core.affiliate_link_tracker
    print(f"✅ core.affiliate_link_tracker")
except Exception as e:
    print(f"❌ core.affiliate_link_tracker: {e}")
    errors.append("core.affiliate_link_tracker")

try:
    import core.ai_host
    print(f"✅ core.ai_host")
except Exception as e:
    print(f"❌ core.ai_host: {e}")
    errors.append("core.ai_host")

try:
    import core.anki_learning_system
    print(f"✅ core.anki_learning_system")
except Exception as e:
    print(f"❌ core.anki_learning_system: {e}")
    errors.append("core.anki_learning_system")

try:
    import core.api_routes
    print(f"✅ core.api_routes")
except Exception as e:
    print(f"❌ core.api_routes: {e}")
    errors.append("core.api_routes")

try:
    import core.api_server
    print(f"✅ core.api_server")
except Exception as e:
    print(f"❌ core.api_server: {e}")
    errors.append("core.api_server")

try:
    import core.audio_enhancer
    print(f"✅ core.audio_enhancer")
except Exception as e:
    print(f"❌ core.audio_enhancer: {e}")
    errors.append("core.audio_enhancer")

try:
    import core.audio_quality
    print(f"✅ core.audio_quality")
except Exception as e:
    print(f"❌ core.audio_quality: {e}")
    errors.append("core.audio_quality")

try:
    import core.audit_database
    print(f"✅ core.audit_database")
except Exception as e:
    print(f"❌ core.audit_database: {e}")
    errors.append("core.audit_database")

try:
    import core.audit_pii_exposure
    print(f"✅ core.audit_pii_exposure")
except Exception as e:
    print(f"❌ core.audit_pii_exposure: {e}")
    errors.append("core.audit_pii_exposure")

try:
    import core.auto_content_generator
    print(f"✅ core.auto_content_generator")
except Exception as e:
    print(f"❌ core.auto_content_generator: {e}")
    errors.append("core.auto_content_generator")

try:
    import core.auto_deploy_domain
    print(f"✅ core.auto_deploy_domain")
except Exception as e:
    print(f"❌ core.auto_deploy_domain: {e}")
    errors.append("core.auto_deploy_domain")

try:
    import core.automation_routes
    print(f"✅ core.automation_routes")
except Exception as e:
    print(f"❌ core.automation_routes: {e}")
    errors.append("core.automation_routes")

try:
    import core.automation_workflows
    print(f"✅ core.automation_workflows")
except Exception as e:
    print(f"❌ core.automation_workflows: {e}")
    errors.append("core.automation_workflows")

try:
    import core.avatar_auto_attach
    print(f"✅ core.avatar_auto_attach")
except Exception as e:
    print(f"❌ core.avatar_auto_attach: {e}")
    errors.append("core.avatar_auto_attach")

try:
    import core.avatar_generator
    print(f"✅ core.avatar_generator")
except Exception as e:
    print(f"❌ core.avatar_generator: {e}")
    errors.append("core.avatar_generator")

try:
    import core.batch_import_posts
    print(f"✅ core.batch_import_posts")
except Exception as e:
    print(f"❌ core.batch_import_posts: {e}")
    errors.append("core.batch_import_posts")

try:
    import core.battle_routes
    print(f"✅ core.battle_routes")
except Exception as e:
    print(f"❌ core.battle_routes: {e}")
    errors.append("core.battle_routes")

try:
    import core.bidirectional_review_engine
    print(f"✅ core.bidirectional_review_engine")
except Exception as e:
    print(f"❌ core.bidirectional_review_engine: {e}")
    errors.append("core.bidirectional_review_engine")

try:
    import core.blamechain
    print(f"✅ core.blamechain")
except Exception as e:
    print(f"❌ core.blamechain: {e}")
    errors.append("core.blamechain")

try:
    import core.blog_syndication
    print(f"✅ core.blog_syndication")
except Exception as e:
    print(f"❌ core.blog_syndication: {e}")
    errors.append("core.blog_syndication")

try:
    import core.brand_ai_orchestrator
    print(f"✅ core.brand_ai_orchestrator")
except Exception as e:
    print(f"❌ core.brand_ai_orchestrator: {e}")
    errors.append("core.brand_ai_orchestrator")

try:
    import core.brand_ai_persona_generator
    print(f"✅ core.brand_ai_persona_generator")
except Exception as e:
    print(f"❌ core.brand_ai_persona_generator: {e}")
    errors.append("core.brand_ai_persona_generator")

try:
    import core.brand_builder
    print(f"✅ core.brand_builder")
except Exception as e:
    print(f"❌ core.brand_builder: {e}")
    errors.append("core.brand_builder")

try:
    import core.brand_creator
    print(f"✅ core.brand_creator")
except Exception as e:
    print(f"❌ core.brand_creator: {e}")
    errors.append("core.brand_creator")

try:
    import core.build
    print(f"✅ core.build")
except Exception as e:
    print(f"❌ core.build: {e}")
    errors.append("core.build")

try:
    import core.build_all
    print(f"✅ core.build_all")
except Exception as e:
    print(f"❌ core.build_all: {e}")
    errors.append("core.build_all")

try:
    import core.build_cringeproof
    print(f"✅ core.build_cringeproof")
except Exception as e:
    print(f"❌ core.build_cringeproof: {e}")
    errors.append("core.build_cringeproof")

try:
    import core.build_from_scratch
    print(f"✅ core.build_from_scratch")
except Exception as e:
    print(f"❌ core.build_from_scratch: {e}")
    errors.append("core.build_from_scratch")

try:
    import core.build_routes
    print(f"✅ core.build_routes")
except Exception as e:
    print(f"❌ core.build_routes: {e}")
    errors.append("core.build_routes")

try:
    import core.business_qr
    print(f"✅ core.business_qr")
except Exception as e:
    print(f"❌ core.business_qr: {e}")
    errors.append("core.business_qr")

try:
    import core.business_routes
    print(f"✅ core.business_routes")
except Exception as e:
    print(f"❌ core.business_routes: {e}")
    errors.append("core.business_routes")

try:
    import core.canvas_integration
    print(f"✅ core.canvas_integration")
except Exception as e:
    print(f"❌ core.canvas_integration: {e}")
    errors.append("core.canvas_integration")

try:
    import core.canvas_routes
    print(f"✅ core.canvas_routes")
except Exception as e:
    print(f"❌ core.canvas_routes: {e}")
    errors.append("core.canvas_routes")

try:
    import core.chapter_version_control
    print(f"✅ core.chapter_version_control")
except Exception as e:
    print(f"❌ core.chapter_version_control: {e}")
    errors.append("core.chapter_version_control")

try:
    import core.chat_routes
    print(f"✅ core.chat_routes")
except Exception as e:
    print(f"❌ core.chat_routes: {e}")
    errors.append("core.chat_routes")

try:
    import core.cleanup_fake_domains
    print(f"✅ core.cleanup_fake_domains")
except Exception as e:
    print(f"❌ core.cleanup_fake_domains: {e}")
    errors.append("core.cleanup_fake_domains")

try:
    import core.comment_github_integration
    print(f"✅ core.comment_github_integration")
except Exception as e:
    print(f"❌ core.comment_github_integration: {e}")
    errors.append("core.comment_github_integration")

try:
    import core.comment_to_post
    print(f"✅ core.comment_to_post")
except Exception as e:
    print(f"❌ core.comment_to_post: {e}")
    errors.append("core.comment_to_post")

try:
    import core.comment_voice_chain
    print(f"✅ core.comment_voice_chain")
except Exception as e:
    print(f"❌ core.comment_voice_chain: {e}")
    errors.append("core.comment_voice_chain")

try:
    import core.content_brand_detector
    print(f"✅ core.content_brand_detector")
except Exception as e:
    print(f"❌ core.content_brand_detector: {e}")
    errors.append("core.content_brand_detector")

try:
    import core.content_generator
    print(f"✅ core.content_generator")
except Exception as e:
    print(f"❌ core.content_generator: {e}")
    errors.append("core.content_generator")

try:
    import core.content_tumbler
    print(f"✅ core.content_tumbler")
except Exception as e:
    print(f"❌ core.content_tumbler: {e}")
    errors.append("core.content_tumbler")

try:
    import core.context_manager
    print(f"✅ core.context_manager")
except Exception as e:
    print(f"❌ core.context_manager: {e}")
    errors.append("core.context_manager")

try:
    import core.contributor_rewards
    print(f"✅ core.contributor_rewards")
except Exception as e:
    print(f"❌ core.contributor_rewards: {e}")
    errors.append("core.contributor_rewards")

try:
    import core.create_blog_post_offline
    print(f"✅ core.create_blog_post_offline")
except Exception as e:
    print(f"❌ core.create_blog_post_offline: {e}")
    errors.append("core.create_blog_post_offline")

try:
    import core.creative_onboarding
    print(f"✅ core.creative_onboarding")
except Exception as e:
    print(f"❌ core.creative_onboarding: {e}")
    errors.append("core.creative_onboarding")

try:
    import core.cringeproof_content_judge
    print(f"✅ core.cringeproof_content_judge")
except Exception as e:
    print(f"❌ core.cringeproof_content_judge: {e}")
    errors.append("core.cringeproof_content_judge")

try:
    import core.cringeproof_personas
    print(f"✅ core.cringeproof_personas")
except Exception as e:
    print(f"❌ core.cringeproof_personas: {e}")
    errors.append("core.cringeproof_personas")

try:
    import core.customer_discovery_backend
    print(f"✅ core.customer_discovery_backend")
except Exception as e:
    print(f"❌ core.customer_discovery_backend: {e}")
    errors.append("core.customer_discovery_backend")

try:
    import core.database
    print(f"✅ core.database")
except Exception as e:
    print(f"❌ core.database: {e}")
    errors.append("core.database")

try:
    import core.db_helpers
    print(f"✅ core.db_helpers")
except Exception as e:
    print(f"❌ core.db_helpers: {e}")
    errors.append("core.db_helpers")

try:
    import core.debug_affiliate_system
    print(f"✅ core.debug_affiliate_system")
except Exception as e:
    print(f"❌ core.debug_affiliate_system: {e}")
    errors.append("core.debug_affiliate_system")

try:
    import core.debug_lab
    print(f"✅ core.debug_lab")
except Exception as e:
    print(f"❌ core.debug_lab: {e}")
    errors.append("core.debug_lab")

try:
    import core.demo_user_journey
    print(f"✅ core.demo_user_journey")
except Exception as e:
    print(f"❌ core.demo_user_journey: {e}")
    errors.append("core.demo_user_journey")

try:
    import core.deploy_tribunal_to_github
    print(f"✅ core.deploy_tribunal_to_github")
except Exception as e:
    print(f"❌ core.deploy_tribunal_to_github: {e}")
    errors.append("core.deploy_tribunal_to_github")

try:
    import core.deployment_diagnostic
    print(f"✅ core.deployment_diagnostic")
except Exception as e:
    print(f"❌ core.deployment_diagnostic: {e}")
    errors.append("core.deployment_diagnostic")

try:
    import core.device_auth
    print(f"✅ core.device_auth")
except Exception as e:
    print(f"❌ core.device_auth: {e}")
    errors.append("core.device_auth")

try:
    import core.dm_via_qr
    print(f"✅ core.dm_via_qr")
except Exception as e:
    print(f"❌ core.dm_via_qr: {e}")
    errors.append("core.dm_via_qr")

try:
    import core.docs_routes
    print(f"✅ core.docs_routes")
except Exception as e:
    print(f"❌ core.docs_routes: {e}")
    errors.append("core.docs_routes")

try:
    import core.domain_chatroom
    print(f"✅ core.domain_chatroom")
except Exception as e:
    print(f"❌ core.domain_chatroom: {e}")
    errors.append("core.domain_chatroom")

try:
    import core.domain_onboarding
    print(f"✅ core.domain_onboarding")
except Exception as e:
    print(f"❌ core.domain_onboarding: {e}")
    errors.append("core.domain_onboarding")

try:
    import core.domain_partnership
    print(f"✅ core.domain_partnership")
except Exception as e:
    print(f"❌ core.domain_partnership: {e}")
    errors.append("core.domain_partnership")

try:
    import core.domain_unlock_engine
    print(f"✅ core.domain_unlock_engine")
except Exception as e:
    print(f"❌ core.domain_unlock_engine: {e}")
    errors.append("core.domain_unlock_engine")

try:
    import core.domain_wordmap_aggregator
    print(f"✅ core.domain_wordmap_aggregator")
except Exception as e:
    print(f"❌ core.domain_wordmap_aggregator: {e}")
    errors.append("core.domain_wordmap_aggregator")

try:
    import core.draw_routes
    print(f"✅ core.draw_routes")
except Exception as e:
    print(f"❌ core.draw_routes: {e}")
    errors.append("core.draw_routes")

try:
    import core.economy_mesh_network
    print(f"✅ core.economy_mesh_network")
except Exception as e:
    print(f"❌ core.economy_mesh_network: {e}")
    errors.append("core.economy_mesh_network")

try:
    import core.enrich_content
    print(f"✅ core.enrich_content")
except Exception as e:
    print(f"❌ core.enrich_content: {e}")
    errors.append("core.enrich_content")

try:
    import core.event_hooks
    print(f"✅ core.event_hooks")
except Exception as e:
    print(f"❌ core.event_hooks: {e}")
    errors.append("core.event_hooks")

try:
    import core.export_brand_filesystem
    print(f"✅ core.export_brand_filesystem")
except Exception as e:
    print(f"❌ core.export_brand_filesystem: {e}")
    errors.append("core.export_brand_filesystem")

try:
    import core.export_static
    print(f"✅ core.export_static")
except Exception as e:
    print(f"❌ core.export_static: {e}")
    errors.append("core.export_static")

try:
    import core.export_voice_recordings
    print(f"✅ core.export_voice_recordings")
except Exception as e:
    print(f"❌ core.export_voice_recordings: {e}")
    errors.append("core.export_voice_recordings")

try:
    import core.file_importer
    print(f"✅ core.file_importer")
except Exception as e:
    print(f"❌ core.file_importer: {e}")
    errors.append("core.file_importer")

try:
    import core.fix_ip_storage
    print(f"✅ core.fix_ip_storage")
except Exception as e:
    print(f"❌ core.fix_ip_storage: {e}")
    errors.append("core.fix_ip_storage")

try:
    import core.folder_router
    print(f"✅ core.folder_router")
except Exception as e:
    print(f"❌ core.folder_router: {e}")
    errors.append("core.folder_router")

try:
    import core.force_claude_write
    print(f"✅ core.force_claude_write")
except Exception as e:
    print(f"❌ core.force_claude_write: {e}")
    errors.append("core.force_claude_write")

try:
    import core.full_flow_demo
    print(f"✅ core.full_flow_demo")
except Exception as e:
    print(f"❌ core.full_flow_demo: {e}")
    errors.append("core.full_flow_demo")

try:
    import core.gallery_routes
    print(f"✅ core.gallery_routes")
except Exception as e:
    print(f"❌ core.gallery_routes: {e}")
    errors.append("core.gallery_routes")

try:
    import core.generate_manifest
    print(f"✅ core.generate_manifest")
except Exception as e:
    print(f"❌ core.generate_manifest: {e}")
    errors.append("core.generate_manifest")

try:
    import core.generator_routes
    print(f"✅ core.generator_routes")
except Exception as e:
    print(f"❌ core.generator_routes: {e}")
    errors.append("core.generator_routes")

try:
    import core.github_faucet
    print(f"✅ core.github_faucet")
except Exception as e:
    print(f"❌ core.github_faucet: {e}")
    errors.append("core.github_faucet")

try:
    import core.github_star_validator
    print(f"✅ core.github_star_validator")
except Exception as e:
    print(f"❌ core.github_star_validator: {e}")
    errors.append("core.github_star_validator")

try:
    import core.gps_encryption
    print(f"✅ core.gps_encryption")
except Exception as e:
    print(f"❌ core.gps_encryption: {e}")
    errors.append("core.gps_encryption")

try:
    import core.hello_world
    print(f"✅ core.hello_world")
except Exception as e:
    print(f"❌ core.hello_world: {e}")
    errors.append("core.hello_world")

try:
    import core.image_admin_routes
    print(f"✅ core.image_admin_routes")
except Exception as e:
    print(f"❌ core.image_admin_routes: {e}")
    errors.append("core.image_admin_routes")

try:
    import core.image_dataset
    print(f"✅ core.image_dataset")
except Exception as e:
    print(f"❌ core.image_dataset: {e}")
    errors.append("core.image_dataset")

try:
    import core.image_workflow
    print(f"✅ core.image_workflow")
except Exception as e:
    print(f"❌ core.image_workflow: {e}")
    errors.append("core.image_workflow")

try:
    import core.import_domains_csv
    print(f"✅ core.import_domains_csv")
except Exception as e:
    print(f"❌ core.import_domains_csv: {e}")
    errors.append("core.import_domains_csv")

try:
    import core.import_domains_simple
    print(f"✅ core.import_domains_simple")
except Exception as e:
    print(f"❌ core.import_domains_simple: {e}")
    errors.append("core.import_domains_simple")

try:
    import core.init_business_db
    print(f"✅ core.init_business_db")
except Exception as e:
    print(f"❌ core.init_business_db: {e}")
    errors.append("core.init_business_db")

try:
    import core.init_kangaroo_court
    print(f"✅ core.init_kangaroo_court")
except Exception as e:
    print(f"❌ core.init_kangaroo_court: {e}")
    errors.append("core.init_kangaroo_court")

try:
    import core.init_knowledge_graph
    print(f"✅ core.init_knowledge_graph")
except Exception as e:
    print(f"❌ core.init_knowledge_graph: {e}")
    errors.append("core.init_knowledge_graph")

try:
    import core.init_learning_cards_for_user
    print(f"✅ core.init_learning_cards_for_user")
except Exception as e:
    print(f"❌ core.init_learning_cards_for_user: {e}")
    errors.append("core.init_learning_cards_for_user")

try:
    import core.init_mesh_economy
    print(f"✅ core.init_mesh_economy")
except Exception as e:
    print(f"❌ core.init_mesh_economy: {e}")
    errors.append("core.init_mesh_economy")

try:
    import core.init_simple_voice
    print(f"✅ core.init_simple_voice")
except Exception as e:
    print(f"❌ core.init_simple_voice: {e}")
    errors.append("core.init_simple_voice")

try:
    import core.init_voice_capsules
    print(f"✅ core.init_voice_capsules")
except Exception as e:
    print(f"❌ core.init_voice_capsules: {e}")
    errors.append("core.init_voice_capsules")

try:
    import core.init_voice_memos_federation
    print(f"✅ core.init_voice_memos_federation")
except Exception as e:
    print(f"❌ core.init_voice_memos_federation: {e}")
    errors.append("core.init_voice_memos_federation")

try:
    import core.inspect-local-system
    print(f"✅ core.inspect-local-system")
except Exception as e:
    print(f"❌ core.inspect-local-system: {e}")
    errors.append("core.inspect-local-system")

try:
    import core.install
    print(f"✅ core.install")
except Exception as e:
    print(f"❌ core.install: {e}")
    errors.append("core.install")

try:
    import core.twitter_integration
    print(f"✅ core.twitter_integration")
except Exception as e:
    print(f"❌ core.twitter_integration: {e}")
    errors.append("core.twitter_integration")

try:
    import core.interactive_onboarding
    print(f"✅ core.interactive_onboarding")
except Exception as e:
    print(f"❌ core.interactive_onboarding: {e}")
    errors.append("core.interactive_onboarding")

try:
    import core.kangaroo_court_routes
    print(f"✅ core.kangaroo_court_routes")
except Exception as e:
    print(f"❌ core.kangaroo_court_routes: {e}")
    errors.append("core.kangaroo_court_routes")

try:
    import core.keyring_unlocks
    print(f"✅ core.keyring_unlocks")
except Exception as e:
    print(f"❌ core.keyring_unlocks: {e}")
    errors.append("core.keyring_unlocks")

try:
    import core.knowledge_extractor
    print(f"✅ core.knowledge_extractor")
except Exception as e:
    print(f"❌ core.knowledge_extractor: {e}")
    errors.append("core.knowledge_extractor")

try:
    import core.license_manager
    print(f"✅ core.license_manager")
except Exception as e:
    print(f"❌ core.license_manager: {e}")
    errors.append("core.license_manager")

try:
    import core.lore_extraction_engine
    print(f"✅ core.lore_extraction_engine")
except Exception as e:
    print(f"❌ core.lore_extraction_engine: {e}")
    errors.append("core.lore_extraction_engine")

try:
    import core.make_it_automatic
    print(f"✅ core.make_it_automatic")
except Exception as e:
    print(f"❌ core.make_it_automatic: {e}")
    errors.append("core.make_it_automatic")

try:
    import core.manage_subscribers
    print(f"✅ core.manage_subscribers")
except Exception as e:
    print(f"❌ core.manage_subscribers: {e}")
    errors.append("core.manage_subscribers")

try:
    import core.membership_system
    print(f"✅ core.membership_system")
except Exception as e:
    print(f"❌ core.membership_system: {e}")
    errors.append("core.membership_system")

try:
    import core.merge_test_to_main
    print(f"✅ core.merge_test_to_main")
except Exception as e:
    print(f"❌ core.merge_test_to_main: {e}")
    errors.append("core.merge_test_to_main")

try:
    import core.migrate_blog_network
    print(f"✅ core.migrate_blog_network")
except Exception as e:
    print(f"❌ core.migrate_blog_network: {e}")
    errors.append("core.migrate_blog_network")

try:
    import core.migrate_chat_transcripts
    print(f"✅ core.migrate_chat_transcripts")
except Exception as e:
    print(f"❌ core.migrate_chat_transcripts: {e}")
    errors.append("core.migrate_chat_transcripts")

try:
    import core.migrate_onboarding_system
    print(f"✅ core.migrate_onboarding_system")
except Exception as e:
    print(f"❌ core.migrate_onboarding_system: {e}")
    errors.append("core.migrate_onboarding_system")

try:
    import core.migrate_stpetepros
    print(f"✅ core.migrate_stpetepros")
except Exception as e:
    print(f"❌ core.migrate_stpetepros: {e}")
    errors.append("core.migrate_stpetepros")

try:
    import core.narrative_cringeproof
    print(f"✅ core.narrative_cringeproof")
except Exception as e:
    print(f"❌ core.narrative_cringeproof: {e}")
    errors.append("core.narrative_cringeproof")

try:
    import core.navigation
    print(f"✅ core.navigation")
except Exception as e:
    print(f"❌ core.navigation: {e}")
    errors.append("core.navigation")

try:
    import core.neural_network
    print(f"✅ core.neural_network")
except Exception as e:
    print(f"❌ core.neural_network: {e}")
    errors.append("core.neural_network")

try:
    import core.neural_soul_scorer
    print(f"✅ core.neural_soul_scorer")
except Exception as e:
    print(f"❌ core.neural_soul_scorer: {e}")
    errors.append("core.neural_soul_scorer")

try:
    import core.notifications
    print(f"✅ core.notifications")
except Exception as e:
    print(f"❌ core.notifications: {e}")
    errors.append("core.notifications")

try:
    import core.nudge_system
    print(f"✅ core.nudge_system")
except Exception as e:
    print(f"❌ core.nudge_system: {e}")
    errors.append("core.nudge_system")

try:
    import core.ollama_auto_commenter
    print(f"✅ core.ollama_auto_commenter")
except Exception as e:
    print(f"❌ core.ollama_auto_commenter: {e}")
    errors.append("core.ollama_auto_commenter")

try:
    import core.ollama_discussion
    print(f"✅ core.ollama_discussion")
except Exception as e:
    print(f"❌ core.ollama_discussion: {e}")
    errors.append("core.ollama_discussion")

try:
    import core.ollama_proxy
    print(f"✅ core.ollama_proxy")
except Exception as e:
    print(f"❌ core.ollama_proxy: {e}")
    errors.append("core.ollama_proxy")

try:
    import core.onboarding_routes
    print(f"✅ core.onboarding_routes")
except Exception as e:
    print(f"❌ core.onboarding_routes: {e}")
    errors.append("core.onboarding_routes")

try:
    import core.one_command_live
    print(f"✅ core.one_command_live")
except Exception as e:
    print(f"❌ core.one_command_live: {e}")
    errors.append("core.one_command_live")

try:
    import core.ownership_rewards
    print(f"✅ core.ownership_rewards")
except Exception as e:
    print(f"❌ core.ownership_rewards: {e}")
    errors.append("core.ownership_rewards")

try:
    import core.plugin_loader
    print(f"✅ core.plugin_loader")
except Exception as e:
    print(f"❌ core.plugin_loader: {e}")
    errors.append("core.plugin_loader")

try:
    import core.post_to_quiz
    print(f"✅ core.post_to_quiz")
except Exception as e:
    print(f"❌ core.post_to_quiz: {e}")
    errors.append("core.post_to_quiz")

try:
    import core.practice_room
    print(f"✅ core.practice_room")
except Exception as e:
    print(f"❌ core.practice_room: {e}")
    errors.append("core.practice_room")

try:
    import core.pre_deploy_check
    print(f"✅ core.pre_deploy_check")
except Exception as e:
    print(f"❌ core.pre_deploy_check: {e}")
    errors.append("core.pre_deploy_check")

try:
    import core.pre_deploy_routes
    print(f"✅ core.pre_deploy_routes")
except Exception as e:
    print(f"❌ core.pre_deploy_routes: {e}")
    errors.append("core.pre_deploy_routes")

try:
    import core.preview_server
    print(f"✅ core.preview_server")
except Exception as e:
    print(f"❌ core.preview_server: {e}")
    errors.append("core.preview_server")

try:
    import core.procedural_media
    print(f"✅ core.procedural_media")
except Exception as e:
    print(f"❌ core.procedural_media: {e}")
    errors.append("core.procedural_media")

try:
    import core.profile_builder
    print(f"✅ core.profile_builder")
except Exception as e:
    print(f"❌ core.profile_builder: {e}")
    errors.append("core.profile_builder")

try:
    import core.progression_system
    print(f"✅ core.progression_system")
except Exception as e:
    print(f"❌ core.progression_system: {e}")
    errors.append("core.progression_system")

try:
    import core.project_launcher
    print(f"✅ core.project_launcher")
except Exception as e:
    print(f"❌ core.project_launcher: {e}")
    errors.append("core.project_launcher")

try:
    import core.proof_of_concept
    print(f"✅ core.proof_of_concept")
except Exception as e:
    print(f"❌ core.proof_of_concept: {e}")
    errors.append("core.proof_of_concept")

try:
    import core.pseo_generator
    print(f"✅ core.pseo_generator")
except Exception as e:
    print(f"❌ core.pseo_generator: {e}")
    errors.append("core.pseo_generator")

try:
    import core.public_comments_api
    print(f"✅ core.public_comments_api")
except Exception as e:
    print(f"❌ core.public_comments_api: {e}")
    errors.append("core.public_comments_api")

try:
    import core.publish_all_brands
    print(f"✅ core.publish_all_brands")
except Exception as e:
    print(f"❌ core.publish_all_brands: {e}")
    errors.append("core.publish_all_brands")

try:
    import core.publish_everywhere
    print(f"✅ core.publish_everywhere")
except Exception as e:
    print(f"❌ core.publish_everywhere: {e}")
    errors.append("core.publish_everywhere")

try:
    import core.publish_to_github
    print(f"✅ core.publish_to_github")
except Exception as e:
    print(f"❌ core.publish_to_github: {e}")
    errors.append("core.publish_to_github")

try:
    import core.publisher_routes
    print(f"✅ core.publisher_routes")
except Exception as e:
    print(f"❌ core.publisher_routes: {e}")
    errors.append("core.publisher_routes")

try:
    import core.qr_analytics
    print(f"✅ core.qr_analytics")
except Exception as e:
    print(f"❌ core.qr_analytics: {e}")
    errors.append("core.qr_analytics")

try:
    import core.qr_auth
    print(f"✅ core.qr_auth")
except Exception as e:
    print(f"❌ core.qr_auth: {e}")
    errors.append("core.qr_auth")

try:
    import core.qr_auto_generate
    print(f"✅ core.qr_auto_generate")
except Exception as e:
    print(f"❌ core.qr_auto_generate: {e}")
    errors.append("core.qr_auto_generate")

try:
    import core.qr_events
    print(f"✅ core.qr_events")
except Exception as e:
    print(f"❌ core.qr_events: {e}")
    errors.append("core.qr_events")

try:
    import core.qr_faucet
    print(f"✅ core.qr_faucet")
except Exception as e:
    print(f"❌ core.qr_faucet: {e}")
    errors.append("core.qr_faucet")

try:
    import core.qr_gallery_system
    print(f"✅ core.qr_gallery_system")
except Exception as e:
    print(f"❌ core.qr_gallery_system: {e}")
    errors.append("core.qr_gallery_system")

try:
    import core.qr_unified
    print(f"✅ core.qr_unified")
except Exception as e:
    print(f"❌ core.qr_unified: {e}")
    errors.append("core.qr_unified")

try:
    import core.qr_user_profile
    print(f"✅ core.qr_user_profile")
except Exception as e:
    print(f"❌ core.qr_user_profile: {e}")
    errors.append("core.qr_user_profile")

try:
    import core.qr_voice_integration
    print(f"✅ core.qr_voice_integration")
except Exception as e:
    print(f"❌ core.qr_voice_integration: {e}")
    errors.append("core.qr_voice_integration")

try:
    import core.query_by_tier
    print(f"✅ core.query_by_tier")
except Exception as e:
    print(f"❌ core.query_by_tier: {e}")
    errors.append("core.query_by_tier")

try:
    import core.query_templates
    print(f"✅ core.query_templates")
except Exception as e:
    print(f"❌ core.query_templates: {e}")
    errors.append("core.query_templates")

try:
    import core.question_routes
    print(f"✅ core.question_routes")
except Exception as e:
    print(f"❌ core.question_routes: {e}")
    errors.append("core.question_routes")

try:
    import core.rate_limiter
    print(f"✅ core.rate_limiter")
except Exception as e:
    print(f"❌ core.rate_limiter: {e}")
    errors.append("core.rate_limiter")

try:
    import core.rotation_helpers
    print(f"✅ core.rotation_helpers")
except Exception as e:
    print(f"❌ core.rotation_helpers: {e}")
    errors.append("core.rotation_helpers")

try:
    import core.scrape_godaddy_landers
    print(f"✅ core.scrape_godaddy_landers")
except Exception as e:
    print(f"❌ core.scrape_godaddy_landers: {e}")
    errors.append("core.scrape_godaddy_landers")

try:
    import core.scrape_live_domains
    print(f"✅ core.scrape_live_domains")
except Exception as e:
    print(f"❌ core.scrape_live_domains: {e}")
    errors.append("core.scrape_live_domains")

try:
    import core.seed_domain_wordmaps
    print(f"✅ core.seed_domain_wordmaps")
except Exception as e:
    print(f"❌ core.seed_domain_wordmaps: {e}")
    errors.append("core.seed_domain_wordmaps")

try:
    import core.seed_domains
    print(f"✅ core.seed_domains")
except Exception as e:
    print(f"❌ core.seed_domains: {e}")
    errors.append("core.seed_domains")

try:
    import core.send_post_email
    print(f"✅ core.send_post_email")
except Exception as e:
    print(f"❌ core.send_post_email: {e}")
    errors.append("core.send_post_email")

try:
    import core.session_sync
    print(f"✅ core.session_sync")
except Exception as e:
    print(f"❌ core.session_sync: {e}")
    errors.append("core.session_sync")

try:
    import core.setup_test_database
    print(f"✅ core.setup_test_database")
except Exception as e:
    print(f"❌ core.setup_test_database: {e}")
    errors.append("core.setup_test_database")

try:
    import core.shortcuts_integration
    print(f"✅ core.shortcuts_integration")
except Exception as e:
    print(f"❌ core.shortcuts_integration: {e}")
    errors.append("core.shortcuts_integration")

try:
    import core.dnd_campaign
    print(f"✅ core.dnd_campaign")
except Exception as e:
    print(f"❌ core.dnd_campaign: {e}")
    errors.append("core.dnd_campaign")

try:
    import core.two_plus_two
    print(f"✅ core.two_plus_two")
except Exception as e:
    print(f"❌ core.two_plus_two: {e}")
    errors.append("core.two_plus_two")

try:
    import core.simple_voice_routes
    print(f"✅ core.simple_voice_routes")
except Exception as e:
    print(f"❌ core.simple_voice_routes: {e}")
    errors.append("core.simple_voice_routes")

try:
    import core.soulfra_assistant
    print(f"✅ core.soulfra_assistant")
except Exception as e:
    print(f"❌ core.soulfra_assistant: {e}")
    errors.append("core.soulfra_assistant")

try:
    import core.soulfra_dark_story
    print(f"✅ core.soulfra_dark_story")
except Exception as e:
    print(f"❌ core.soulfra_dark_story: {e}")
    errors.append("core.soulfra_dark_story")

try:
    import core.start
    print(f"✅ core.start")
except Exception as e:
    print(f"❌ core.start: {e}")
    errors.append("core.start")

try:
    import core.start_demo
    print(f"✅ core.start_demo")
except Exception as e:
    print(f"❌ core.start_demo: {e}")
    errors.append("core.start_demo")

try:
    import core.status_routes
    print(f"✅ core.status_routes")
except Exception as e:
    print(f"❌ core.status_routes: {e}")
    errors.append("core.status_routes")

try:
    import core.studio_api
    print(f"✅ core.studio_api")
except Exception as e:
    print(f"❌ core.studio_api: {e}")
    errors.append("core.studio_api")

try:
    import core.subdomain_router
    print(f"✅ core.subdomain_router")
except Exception as e:
    print(f"❌ core.subdomain_router: {e}")
    errors.append("core.subdomain_router")

try:
    import core.template_orchestrator
    print(f"✅ core.template_orchestrator")
except Exception as e:
    print(f"❌ core.template_orchestrator: {e}")
    errors.append("core.template_orchestrator")

try:
    import core.test_domain_diversity
    print(f"✅ core.test_domain_diversity")
except Exception as e:
    print(f"❌ core.test_domain_diversity: {e}")
    errors.append("core.test_domain_diversity")

try:
    import core.test_everything
    print(f"✅ core.test_everything")
except Exception as e:
    print(f"❌ core.test_everything: {e}")
    errors.append("core.test_everything")

try:
    import core.test_flow
    print(f"✅ core.test_flow")
except Exception as e:
    print(f"❌ core.test_flow: {e}")
    errors.append("core.test_flow")

try:
    import core.test_full_pipeline
    print(f"✅ core.test_full_pipeline")
except Exception as e:
    print(f"❌ core.test_full_pipeline: {e}")
    errors.append("core.test_full_pipeline")

try:
    import core.test_gallery_integration
    print(f"✅ core.test_gallery_integration")
except Exception as e:
    print(f"❌ core.test_gallery_integration: {e}")
    errors.append("core.test_gallery_integration")

try:
    import core.test_handle_system
    print(f"✅ core.test_handle_system")
except Exception as e:
    print(f"❌ core.test_handle_system: {e}")
    errors.append("core.test_handle_system")

try:
    import core.test_hello_world
    print(f"✅ core.test_hello_world")
except Exception as e:
    print(f"❌ core.test_hello_world: {e}")
    errors.append("core.test_hello_world")

try:
    import core.test_idea_board
    print(f"✅ core.test_idea_board")
except Exception as e:
    print(f"❌ core.test_idea_board: {e}")
    errors.append("core.test_idea_board")

try:
    import core.test_integration_flow
    print(f"✅ core.test_integration_flow")
except Exception as e:
    print(f"❌ core.test_integration_flow: {e}")
    errors.append("core.test_integration_flow")

try:
    import core.test_network_stack
    print(f"✅ core.test_network_stack")
except Exception as e:
    print(f"❌ core.test_network_stack: {e}")
    errors.append("core.test_network_stack")

try:
    import core.test_qr_flow
    print(f"✅ core.test_qr_flow")
except Exception as e:
    print(f"❌ core.test_qr_flow: {e}")
    errors.append("core.test_qr_flow")

try:
    import core.test_signup
    print(f"✅ core.test_signup")
except Exception as e:
    print(f"❌ core.test_signup: {e}")
    errors.append("core.test_signup")

try:
    import core.test_system
    print(f"✅ core.test_system")
except Exception as e:
    print(f"❌ core.test_system: {e}")
    errors.append("core.test_system")

try:
    import core.test_voice_integration
    print(f"✅ core.test_voice_integration")
except Exception as e:
    print(f"❌ core.test_voice_integration: {e}")
    errors.append("core.test_voice_integration")

try:
    import core.tier_progression_engine
    print(f"✅ core.tier_progression_engine")
except Exception as e:
    print(f"❌ core.tier_progression_engine: {e}")
    errors.append("core.tier_progression_engine")

try:
    import core.token_purchase_system
    print(f"✅ core.token_purchase_system")
except Exception as e:
    print(f"❌ core.token_purchase_system: {e}")
    errors.append("core.token_purchase_system")

try:
    import core.token_routes
    print(f"✅ core.token_routes")
except Exception as e:
    print(f"❌ core.token_routes: {e}")
    errors.append("core.token_routes")

try:
    import core.train_context_networks
    print(f"✅ core.train_context_networks")
except Exception as e:
    print(f"❌ core.train_context_networks: {e}")
    errors.append("core.train_context_networks")

try:
    import core.train_topic_networks
    print(f"✅ core.train_topic_networks")
except Exception as e:
    print(f"❌ core.train_topic_networks: {e}")
    errors.append("core.train_topic_networks")

try:
    import core.transcript_aggregator
    print(f"✅ core.transcript_aggregator")
except Exception as e:
    print(f"❌ core.transcript_aggregator: {e}")
    errors.append("core.transcript_aggregator")

try:
    import core.tribunal_blamechain
    print(f"✅ core.tribunal_blamechain")
except Exception as e:
    print(f"❌ core.tribunal_blamechain: {e}")
    errors.append("core.tribunal_blamechain")

try:
    import core.tutorial_builder
    print(f"✅ core.tutorial_builder")
except Exception as e:
    print(f"❌ core.tutorial_builder: {e}")
    errors.append("core.tutorial_builder")

try:
    import core.unified_generator
    print(f"✅ core.unified_generator")
except Exception as e:
    print(f"❌ core.unified_generator: {e}")
    errors.append("core.unified_generator")

try:
    import core.unified_logger
    print(f"✅ core.unified_logger")
except Exception as e:
    print(f"❌ core.unified_logger: {e}")
    errors.append("core.unified_logger")

try:
    import core.url_shortener
    print(f"✅ core.url_shortener")
except Exception as e:
    print(f"❌ core.url_shortener: {e}")
    errors.append("core.url_shortener")

try:
    import core.url_to_blog
    print(f"✅ core.url_to_blog")
except Exception as e:
    print(f"❌ core.url_to_blog: {e}")
    errors.append("core.url_to_blog")

try:
    import core.url_to_email
    print(f"✅ core.url_to_email")
except Exception as e:
    print(f"❌ core.url_to_email: {e}")
    errors.append("core.url_to_email")

try:
    import core.user_data_export
    print(f"✅ core.user_data_export")
except Exception as e:
    print(f"❌ core.user_data_export: {e}")
    errors.append("core.user_data_export")

try:
    import core.user_economy
    print(f"✅ core.user_economy")
except Exception as e:
    print(f"❌ core.user_economy: {e}")
    errors.append("core.user_economy")

try:
    import core.user_pairing
    print(f"✅ core.user_pairing")
except Exception as e:
    print(f"❌ core.user_pairing: {e}")
    errors.append("core.user_pairing")

try:
    import core.user_wordmap_engine
    print(f"✅ core.user_wordmap_engine")
except Exception as e:
    print(f"❌ core.user_wordmap_engine: {e}")
    errors.append("core.user_wordmap_engine")

try:
    import core.user_workspace
    print(f"✅ core.user_workspace")
except Exception as e:
    print(f"❌ core.user_workspace: {e}")
    errors.append("core.user_workspace")

try:
    import core.vanity_qr
    print(f"✅ core.vanity_qr")
except Exception as e:
    print(f"❌ core.vanity_qr: {e}")
    errors.append("core.vanity_qr")

try:
    import core.verify_image
    print(f"✅ core.verify_image")
except Exception as e:
    print(f"❌ core.verify_image: {e}")
    errors.append("core.verify_image")

try:
    import core.verify_import
    print(f"✅ core.verify_import")
except Exception as e:
    print(f"❌ core.verify_import: {e}")
    errors.append("core.verify_import")

try:
    import core.verify_mvp_integration
    print(f"✅ core.verify_mvp_integration")
except Exception as e:
    print(f"❌ core.verify_mvp_integration: {e}")
    errors.append("core.verify_mvp_integration")

try:
    import core.voice_bank_routes
    print(f"✅ core.voice_bank_routes")
except Exception as e:
    print(f"❌ core.voice_bank_routes: {e}")
    errors.append("core.voice_bank_routes")

try:
    import core.voice_capsule_engine
    print(f"✅ core.voice_capsule_engine")
except Exception as e:
    print(f"❌ core.voice_capsule_engine: {e}")
    errors.append("core.voice_capsule_engine")

try:
    import core.voice_capsule_routes
    print(f"✅ core.voice_capsule_routes")
except Exception as e:
    print(f"❌ core.voice_capsule_routes: {e}")
    errors.append("core.voice_capsule_routes")

try:
    import core.voice_captcha
    print(f"✅ core.voice_captcha")
except Exception as e:
    print(f"❌ core.voice_captcha: {e}")
    errors.append("core.voice_captcha")

try:
    import core.voice_content_generator
    print(f"✅ core.voice_content_generator")
except Exception as e:
    print(f"❌ core.voice_content_generator: {e}")
    errors.append("core.voice_content_generator")

try:
    import core.voice_domain_creator_routes
    print(f"✅ core.voice_domain_creator_routes")
except Exception as e:
    print(f"❌ core.voice_domain_creator_routes: {e}")
    errors.append("core.voice_domain_creator_routes")

try:
    import core.voice_federation_routes
    print(f"✅ core.voice_federation_routes")
except Exception as e:
    print(f"❌ core.voice_federation_routes: {e}")
    errors.append("core.voice_federation_routes")

try:
    import core.voice_health
    print(f"✅ core.voice_health")
except Exception as e:
    print(f"❌ core.voice_health: {e}")
    errors.append("core.voice_health")

try:
    import core.voice_health_checker
    print(f"✅ core.voice_health_checker")
except Exception as e:
    print(f"❌ core.voice_health_checker: {e}")
    errors.append("core.voice_health_checker")

try:
    import core.voice_idea_board_routes
    print(f"✅ core.voice_idea_board_routes")
except Exception as e:
    print(f"❌ core.voice_idea_board_routes: {e}")
    errors.append("core.voice_idea_board_routes")

try:
    import core.voice_input
    print(f"✅ core.voice_input")
except Exception as e:
    print(f"❌ core.voice_input: {e}")
    errors.append("core.voice_input")

try:
    import core.voice_ollama_processor
    print(f"✅ core.voice_ollama_processor")
except Exception as e:
    print(f"❌ core.voice_ollama_processor: {e}")
    errors.append("core.voice_ollama_processor")

try:
    import core.voice_podcast_chapters
    print(f"✅ core.voice_podcast_chapters")
except Exception as e:
    print(f"❌ core.voice_podcast_chapters: {e}")
    errors.append("core.voice_podcast_chapters")

try:
    import core.voice_routes
    print(f"✅ core.voice_routes")
except Exception as e:
    print(f"❌ core.voice_routes: {e}")
    errors.append("core.voice_routes")

try:
    import core.voice_seo_pattern_detector
    print(f"✅ core.voice_seo_pattern_detector")
except Exception as e:
    print(f"❌ core.voice_seo_pattern_detector: {e}")
    errors.append("core.voice_seo_pattern_detector")

try:
    import core.web_domain_manager_routes
    print(f"✅ core.web_domain_manager_routes")
except Exception as e:
    print(f"❌ core.web_domain_manager_routes: {e}")
    errors.append("core.web_domain_manager_routes")

try:
    import core.websocket_server
    print(f"✅ core.websocket_server")
except Exception as e:
    print(f"❌ core.websocket_server: {e}")
    errors.append("core.websocket_server")

try:
    import core.whisper_processor
    print(f"✅ core.whisper_processor")
except Exception as e:
    print(f"❌ core.whisper_processor: {e}")
    errors.append("core.whisper_processor")

try:
    import core.widget_qr_bridge
    print(f"✅ core.widget_qr_bridge")
except Exception as e:
    print(f"❌ core.widget_qr_bridge: {e}")
    errors.append("core.widget_qr_bridge")

try:
    import core.widget_router
    print(f"✅ core.widget_router")
except Exception as e:
    print(f"❌ core.widget_router: {e}")
    errors.append("core.widget_router")

try:
    import core.wiki_concepts
    print(f"✅ core.wiki_concepts")
except Exception as e:
    print(f"❌ core.wiki_concepts: {e}")
    errors.append("core.wiki_concepts")

try:
    import core.wordmap_pitch_integrator
    print(f"✅ core.wordmap_pitch_integrator")
except Exception as e:
    print(f"❌ core.wordmap_pitch_integrator: {e}")
    errors.append("core.wordmap_pitch_integrator")

try:
    import core.workflow_routes
    print(f"✅ core.workflow_routes")
except Exception as e:
    print(f"❌ core.workflow_routes: {e}")
    errors.append("core.workflow_routes")

# Test optional imports
try:
    import optional.app
    print(f"✅ optional.app")
except Exception as e:
    print(f"❌ optional.app: {e}")
    errors.append("optional.app")

try:
    import optional.backfill_mesh_network
    print(f"✅ optional.backfill_mesh_network")
except Exception as e:
    print(f"❌ optional.backfill_mesh_network: {e}")
    errors.append("optional.backfill_mesh_network")

try:
    import optional.github_watcher
    print(f"✅ optional.github_watcher")
except Exception as e:
    print(f"❌ optional.github_watcher: {e}")
    errors.append("optional.github_watcher")

try:
    import optional.ollama_email_node
    print(f"✅ optional.ollama_email_node")
except Exception as e:
    print(f"❌ optional.ollama_email_node: {e}")
    errors.append("optional.ollama_email_node")

try:
    import optional.prove_voice_pipeline
    print(f"✅ optional.prove_voice_pipeline")
except Exception as e:
    print(f"❌ optional.prove_voice_pipeline: {e}")
    errors.append("optional.prove_voice_pipeline")

try:
    import optional.simple_emailer
    print(f"✅ optional.simple_emailer")
except Exception as e:
    print(f"❌ optional.simple_emailer: {e}")
    errors.append("optional.simple_emailer")

try:
    import optional.test_mesh_flow
    print(f"✅ optional.test_mesh_flow")
except Exception as e:
    print(f"❌ optional.test_mesh_flow: {e}")
    errors.append("optional.test_mesh_flow")

try:
    import optional.tribunal_email_notifier
    print(f"✅ optional.tribunal_email_notifier")
except Exception as e:
    print(f"❌ optional.tribunal_email_notifier: {e}")
    errors.append("optional.tribunal_email_notifier")

try:
    import optional.whisper_transcriber
    print(f"✅ optional.whisper_transcriber")
except Exception as e:
    print(f"❌ optional.whisper_transcriber: {e}")
    errors.append("optional.whisper_transcriber")

print()
if errors:
    print(f"❌ {len(errors)} import errors")
    sys.exit(1)
else:
    print("🎉 All imports work!")
    sys.exit(0)
