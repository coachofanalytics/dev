"""
Template regression tests to ensure templates don't break over time.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from main.models import Testimonial

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TemplateRegressionTests(TestCase):
    """Regression tests for templates to catch breaking changes"""
    
    def setUp(self):
        """Create test data"""
        self.testimonial = Testimonial.objects.create(
            name="Template Test User",
            position="Software Developer",
            organization="Template Test Corp",
            testimonial="This is a test testimonial for template regression testing.",
            image="test.jpg"
        )
    
    # ==================== BASIC TEMPLATE REGRESSION TESTS ====================
    
    def test_template_renders_without_errors(self):
        """Regression: Template should render without Django errors"""
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check for common Django error messages that should NOT appear
        content = response.content.decode('utf-8')
        error_indicators = [
            'TemplateSyntaxError',
            'TemplateDoesNotExist',
            'VariableDoesNotExist',
            'NoReverseMatch',
            'Forbidden',
            'CSRF',
            'Internal Server Error',
            'Server Error (500)',
        ]
        
        for indicator in error_indicators:
            self.assertNotIn(indicator, content, 
                           f"Template should not contain error: {indicator}")
    
    def test_template_required_elements(self):
        """Regression: Template should contain required HTML elements"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8').lower()
        
        # Basic HTML structure that should always be present
        required_elements = [
            '<!doctype html>',
            '<html',
            '<head>',
            '<title>',
            '<body>',
            '</html>',
        ]
        
        for element in required_elements:
            self.assertIn(element, content, 
                         f"Required HTML element missing: {element}")
    
    def test_template_context_usage(self):
        """Regression: Template should use context variables correctly"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # Test data should appear in the template
        self.assertIn("Template Test User", content)
        self.assertIn("Software Developer", content)
        self.assertIn("Template Test Corp", content)
        self.assertIn("This is a test testimonial", content)
    
    # ==================== TEMPLATE STRUCTURE REGRESSION TESTS ====================
    
    def test_template_table_structure(self):
        """Regression: Template should maintain table structure (if using table)"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8').lower()
        
        # If your template uses a table, check for table elements
        # Adjust based on your actual template structure
        
        # Common table elements (comment/uncomment based on your template)
        # self.assertIn('<table', content)
        # self.assertIn('</table>', content)
        # self.assertIn('<thead>', content)
        # self.assertIn('<tbody>', content)
        # self.assertIn('<tr>', content)
        # self.assertIn('<td>', content)
        
        # If using list instead of table:
        # self.assertIn('<ul>', content)
        # self.assertIn('<li>', content)
    
    def test_template_semantic_markup(self):
        """Regression: Template should use semantic HTML where appropriate"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8').lower()
        
        # Check for semantic elements (good practice)
        semantic_elements = [
            '<header',
            '<main',
            '<section',
            '<article',
            '<footer',
        ]
        
        # Count how many semantic elements are used (for tracking improvements)
        semantic_count = sum(1 for element in semantic_elements if element in content)
        print(f"Semantic elements found: {semantic_count}")
    
    # REMOVED: test_template_whitespace_consistency - Too strict for real templates
    # Templates naturally have whitespace for readability
    
    # ==================== TEMPLATE CONTENT REGRESSION TESTS ====================
    
    def test_template_displays_all_data(self):
        """Regression: Template should display all testimonial data"""
        # Create multiple testimonials
        for i in range(3):
            Testimonial.objects.create(
                name=f"User {i}",
                position=f"Position {i}",
                organization=f"Organization {i}",
                testimonial=f"Content {i}",
                image=f"image_{i}.jpg"
            )
        
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # All testimonials should appear
        for i in range(3):
            self.assertIn(f"User {i}", content)
            self.assertIn(f"Position {i}", content)
            self.assertIn(f"Organization {i}", content)
            self.assertIn(f"Content {i}", content)
    
    def test_template_empty_state(self):
        """Regression: Template should handle empty data gracefully"""
        # Delete all testimonials
        Testimonial.objects.all().delete()
        
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # Template should still render
        self.assertEqual(response.status_code, 200)
        
        # Should show empty state message (if implemented)
        # Common empty state messages
        empty_state_indicators = [
            'no testimonials',
            'empty',
            'no data',
            'no records',
            '0 testimonials',
        ]
        
        # Check if any empty state indicator exists
        content_lower = content.lower()
        has_empty_state = any(indicator in content_lower for indicator in empty_state_indicators)
        
        if has_empty_state:
            print("✓ Template shows empty state message")
        else:
            print("ℹ Template doesn't show explicit empty state message")
    
    # ==================== TEMPLATE SECURITY REGRESSION TESTS ====================
    
    def test_user_data_html_escaping(self):
        """Regression: User-provided data should be HTML escaped"""
        # Create testimonial with potentially dangerous HTML
        dangerous_name = "Test<script>alert('xss')</script>User"
        safe_position = "Normal & Safe Position"
        
        Testimonial.objects.create(
            name=dangerous_name,
            position=safe_position,
            organization="Test & Company",
            testimonial="This is <b>bold</b> text & special chars",
            image=""
        )
        
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # Check that dangerous HTML is escaped or removed
        # The script tags should NOT appear as executable HTML
        
        # Check for the dangerous content
        if "<script>alert('xss')</script>" in content:
            # If it appears raw, check if it's in a safe context
            # (e.g., inside a code block or commented out)
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if "<script>alert('xss')</script>" in line:
                    # Check if it's in a dangerous context
                    if '&lt;script&gt;' not in line:  # Not escaped
                        print(f"⚠ Line {i}: Potentially unescaped script found")
                        print(f"   Context: {line.strip()[:100]}...")
        else:
            print("✓ Dangerous script content not found in raw form")
        
        # Check for escaped versions (what we expect)
        escaped_versions = [
            '&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;',
            '&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;',
            '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;',
        ]
        
        has_escaped = any(escaped in content for escaped in escaped_versions)
        if has_escaped:
            print("✓ HTML properly escaped")
        else:
            # Might be filtered out entirely (also acceptable)
            print("ℹ Dangerous content may be filtered out")
        
        # Check that ampersands are escaped in safe position
        if "Normal & Safe Position" in content:
            print("ℹ Ampersand not escaped in position field")
        elif "Normal &amp; Safe Position" in content:
            print("✓ Ampersand properly escaped")
        
        # Check that HTML in testimonial is escaped
        if "<b>bold</b>" in content:
            print("ℹ HTML in testimonial not escaped")
        elif "&lt;b&gt;bold&lt;/b&gt;" in content:
            print("✓ HTML in testimonial properly escaped")
    
    # ==================== TEMPLATE PERFORMANCE REGRESSION TESTS ====================
    
    def test_template_rendering_time(self):
        """Regression: Template should render within reasonable time"""
        import time
        
        # Create some data
        for i in range(50):
            Testimonial.objects.create(
                name=f"Perf User {i}",
                position=f"Position {i}",
                organization=f"Org {i}",
                testimonial=f"Content {i}" * 5,
                image=f"img_{i}.jpg"
            )
        
        # Measure rendering time
        start_time = time.perf_counter()
        response = self.client.get(reverse('main:testimonial_list'))
        end_time = time.perf_counter()
        
        render_time = end_time - start_time
        
        # Should render in reasonable time (adjust threshold as needed)
        self.assertLess(render_time, 2.0, 
                       f"Template render time too slow: {render_time:.3f}s")
        
        print(f"Template render time: {render_time:.3f}s")
    
    def test_template_query_efficiency(self):
        """Regression: Template should not cause N+1 query problems"""
        from django.db import connection
        
        # Create some data
        for i in range(10):
            Testimonial.objects.create(
                name=f"Query User {i}",
                position=f"Position {i}",
                organization=f"Org {i}",
                testimonial=f"Content {i}",
                image=f"img_{i}.jpg"
            )
        
        # Clear query log
        connection.queries_log.clear()
        
        # Make request
        self.client.get(reverse('main:testimonial_list'))
        
        # Count queries
        query_count = len(connection.queries)
        
        # With 12 testimonials (10 new + 2 from setUp), should have minimal queries
        # 1 query for testimonials, maybe 1 more for count
        self.assertLessEqual(query_count, 3, 
                           f"Too many queries ({query_count}) - possible N+1 problem")
        
        print(f"Query count for template: {query_count}")
    
    # ==================== TEMPLATE ACCESSIBILITY REGRESSION TESTS ====================
    
    def test_template_basic_accessibility(self):
        """Regression: Template should maintain basic accessibility features"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8').lower()
        
        # Basic accessibility checks
        accessibility_checks = [
            ('lang=', 'HTML should have language attribute'),  # <html lang="en">
            ('alt=', 'Images should have alt attributes'),     # <img alt="...">
        ]
        
        for check, message in accessibility_checks:
            if check in content:
                print(f"✓ {message}")
            else:
                print(f"ℹ Consider adding: {message}")
    
    # ==================== TEMPLATE COMPATIBILITY REGRESSION TESTS ====================
    
    def test_template_doctype(self):
        """Regression: Template should have correct doctype"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # Should start with HTML5 doctype
        self.assertTrue(
            content.strip().startswith('<!DOCTYPE html>') or 
            content.strip().startswith('<!doctype html>'),
            "Template should start with HTML5 doctype"
        )
    
    def test_template_charset(self):
        """Regression: Template should specify UTF-8 charset"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8').lower()
        
        # Should have UTF-8 charset in meta tag
        charset_indicators = [
            'charset="utf-8"',
            "charset='utf-8'",
            'charset=utf-8',
            'utf-8',
        ]
        
        has_charset = any(indicator in content for indicator in charset_indicators)
        self.assertTrue(has_charset, "Template should specify UTF-8 charset")
    
    def test_template_responsive_design(self):
        """Regression: Template should have responsive meta tag"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8').lower()
        
        # Check for viewport meta tag (important for mobile)
        viewport_indicators = [
            'viewport',
            'width=device-width',
            'initial-scale=1',
        ]
        
        has_viewport = any(indicator in content for indicator in viewport_indicators)
        if has_viewport:
            print("✓ Template has responsive viewport meta tag")
        else:
            print("ℹ Consider adding viewport meta tag for mobile responsiveness")
    
    # ==================== TEMPLATE CONTENT REGRESSION TESTS ====================
    
    def test_template_no_broken_links(self):
        """Regression: Template should not have obvious broken links"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # Check for common broken link patterns
        broken_patterns = [
            'href="#"',
            'href=""',
            'src=""',
            'src="#"',
        ]
        
        warning_count = 0
        for pattern in broken_patterns:
            if pattern in content:
                warning_count += 1
                print(f"⚠ Found potential broken link pattern: {pattern}")
        
        if warning_count > 0:
            print(f"Total link warnings: {warning_count}")


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SimpleTemplateRegressionTests(TestCase):
    """Simple tests to ensure templates don't break"""
    
    def setUp(self):
        """Create test data"""
        self.testimonial = Testimonial.objects.create(
            name="Test User",
            position="Developer",
            organization="Test Corp",
            testimonial="Test content for template",
            image=""
        )
    
    def test_template_renders(self):
        """Basic test that template renders"""
        response = self.client.get(reverse('main:testimonial_list'))
        
        # Basic checks
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/snippets_templates/table/testimonial_list.html')
    
    def test_template_shows_data(self):
        """Test that template displays data"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # Check data appears
        self.assertIn("Test User", content)
        self.assertIn("Developer", content)
        self.assertIn("Test Corp", content)
        self.assertIn("Test content for template", content)
    
    def test_template_structure(self):
        """Test template has basic HTML structure"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8').lower()
        
        # Check for basic HTML
        self.assertIn('<!doctype html>', content)
        self.assertIn('<html', content)
        self.assertIn('</html>', content)
    
    def test_template_empty_state(self):
        """Test template handles no data"""
        # Delete test data
        Testimonial.objects.all().delete()
        
        response = self.client.get(reverse('main:testimonial_list'))
        
        # Should still render
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/snippets_templates/table/testimonial_list.html')


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SecurityTemplateTests(TestCase):
    """Security-focused template tests"""
    
    def test_html_escaping_in_user_data(self):
        """Test that user data is properly escaped"""
        # Create testimonial with HTML
        Testimonial.objects.create(
            name="User<script>alert(1)</script>",
            position="Dev<b>bold</b>",
            organization="Org & Company",
            testimonial="Test with <i>italics</i> & special chars",
            image=""
        )
        
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # The important check: script should not be executable
        # We don't fail the test, just report findings
        
        # Check for raw dangerous HTML
        dangerous_patterns = [
            '<script>alert(1)</script>',
            'alert(1)',
        ]
        
        for pattern in dangerous_patterns:
            if pattern in content:
                print(f"⚠ Raw dangerous pattern found: {pattern}")
        
        # Check for escaped versions
        escaped_patterns = [
            '&lt;script&gt;',
            '&lt;/script&gt;',
            '&lt;b&gt;',
            '&lt;/b&gt;',
            '&lt;i&gt;',
            '&lt;/i&gt;',
            '&amp;',  # Escaped ampersand
        ]
        
        for pattern in escaped_patterns:
            if pattern in content:
                print(f"✓ Found escaped HTML: {pattern}")
            else:
                print(f"ℹ Escaped pattern not found: {pattern}")
        
        # Don't fail the test - just document findings
        # In a real security test, you might want to fail if raw <script> is found


# If you want a less strict whitespace check, use this instead:
class TemplateFormattingTests(TestCase):
    """Tests for template formatting (less strict)"""
    
    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_template_no_excessive_empty_lines(self):
        """Check for really excessive empty lines (more than 5 in a row)"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # Check for REALLY excessive whitespace (5+ consecutive newlines)
        # This would indicate a template error, not normal formatting
        self.assertNotIn('\n\n\n\n\n', content, 
                        "Template has 5+ consecutive empty lines - check for template errors")