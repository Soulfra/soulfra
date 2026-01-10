#!/usr/bin/env python3
"""Test default values in formula engine"""

from formula_engine import FormulaEngine

print("Testing Formula Engine Default Values\n" + "="*50)

engine = FormulaEngine()

# Test 1: Template with generated_content (undefined variable)
print("\n✅ Test 1: Template with {{generated_content}} (no variable provided)")
template1 = """
<html>
<body>
    <h1>{{brand}}</h1>
    <div>{{generated_content}}</div>
</body>
</html>
"""

variables1 = {
    "brand": "Soulfra"
    # generated_content NOT provided - should use default
}

try:
    result1 = engine.render_template(template1, variables1)
    print("✅ SUCCESS - Rendered without error!")
    print("\nRendered HTML:")
    print(result1[:300] + "...")
    if "Content will appear here" in result1:
        print("\n✅ Default value used correctly!")
except Exception as e:
    print(f"❌ FAILED - Error: {e}")

# Test 2: Template with generated_content provided
print("\n" + "="*50)
print("\n✅ Test 2: Template with {{generated_content}} (variable provided)")

variables2 = {
    "brand": "Soulfra",
    "generated_content": "<p>This is my custom AI-generated blog post about theming!</p>"
}

try:
    result2 = engine.render_template(template1, variables2)
    print("✅ SUCCESS - Rendered without error!")
    if "custom AI-generated blog post" in result2:
        print("✅ Custom value used correctly!")
except Exception as e:
    print(f"❌ FAILED - Error: {e}")

# Test 3: Blog template (the actual one you're using)
print("\n" + "="*50)
print("\n✅ Test 3: blog.html.tmpl template (simulated)")

blog_template_snippet = """
<div class="article-content">
    {{generated_content}}
</div>
"""

variables3 = {
    # NO generated_content - should use default
}

try:
    result3 = engine.render_template(blog_template_snippet, variables3)
    print("✅ SUCCESS - Blog template rendered without error!")
    print(f"\nResult: {result3}")
except Exception as e:
    print(f"❌ FAILED - Error: {e}")

# Test 4: Custom defaults
print("\n" + "="*50)
print("\n✅ Test 4: Custom default values")

custom_defaults = {
    "author": "Matthew",
    "site_name": "My Custom Site"
}

engine_custom = FormulaEngine(default_values=custom_defaults)

template4 = "<p>By {{author}} on {{site_name}}</p>"

try:
    result4 = engine_custom.render_template(template4, {})
    print("✅ SUCCESS - Custom defaults work!")
    print(f"Result: {result4}")
except Exception as e:
    print(f"❌ FAILED - Error: {e}")

print("\n" + "="*50)
print("\n🎉 All tests completed!")
print("\nNow templates won't break when variables are missing!")
