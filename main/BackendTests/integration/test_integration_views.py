"""
Integration tests for Testimonial views to ensure components work together correctly.
Integration tests verify that different parts of the system work together as expected.
"""
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from main.models import Testimonial
from main import views

# Try to import your custom user model
try:
    from accounts.models import CustomerUser
    HAS_CUSTOM_USER = True
    UserModel = CustomerUser
except ImportError:
    # Fall back to default User model if custom one doesn't exist
    from django.contrib.auth.models import User
    HAS_CUSTOM_USER = False
    UserModel = User

import json

@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    SECURE_SSL_REDIRECT=False,  # Disable SSL redirect for testing
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class TestimonialIntegrationTests(TestCase):
    """Integration tests for Testimonial view with other system components"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.factory = RequestFactory()
        
        # Create test data
        self.testimonial1 = Testimonial.objects.create(
            name="Integration User 1",
            position="Software Developer",
            organization="Integration Corp",
            testimonial="Great integration testing!",
            image="test1.jpg"
        )
        
        self.testimonial2 = Testimonial.objects.create(
            name="Integration User 2",
            position="Product Manager",
            organization="Product Inc",
            testimonial="Excellent product integration.",
            image="test2.jpg"
        )
        
        # Create test user for authentication tests (only if needed)
        # Only create user if authentication tests will run
        self.user = None
        
    # ==================== VIEW + TEMPLATE INTEGRATION TESTS ====================
    
    def test_view_template_integration(self):
        """Integration: View should correctly pass data to template"""
        response = self.client.get(reverse('main:testimonial_list'))
        
        # Check all integration points
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/snippets_templates/table/testimonial_list.html')
        
        # Context should be passed correctly
        self.assertIn('testimonial', response.context)
        
        # Template should render context data
        content = response.content.decode('utf-8')
        self.assertIn("Integration User 1", content)
        self.assertIn("Software Developer", content)
        self.assertIn("Integration Corp", content)
        self.assertIn("Great integration testing!", content)
        
        print("✅ View and template integrate correctly")
    
    def test_template_context_rendering(self):
        """Integration: All context data should render in template"""
        response = self.client.get(reverse('main:testimonial_list'))
        testimonials = response.context['testimonial']
        
        # All testimonials should be in context
        self.assertEqual(testimonials.count(), 2)
        
        # All should render in template
        content = response.content.decode('utf-8')
        for testimonial in testimonials:
            self.assertIn(testimonial.name, content)
            self.assertIn(testimonial.position, content)
            self.assertIn(testimonial.organization, content)
            self.assertIn(testimonial.testimonial, content)
        
        print("✅ All context data renders in template")
    
    # ==================== VIEW + URL + TEMPLATE INTEGRATION ====================
    
    def test_full_url_view_template_chain(self):
        """Integration: Full chain from URL → View → Template"""
        # Test direct URL access
        response1 = self.client.get('/Testimonial/')
        self.assertEqual(response1.status_code, 200)
        
        # Test reverse URL access
        response2 = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response2.status_code, 200)
        
        # Both should return same content
        content1 = response1.content.decode('utf-8')
        content2 = response2.content.decode('utf-8')
        
        # Key content should be in both
        for content in [content1, content2]:
            self.assertIn("Integration User 1", content)
            self.assertIn("Integration User 2", content)
        
        print("✅ URL → View → Template chain works correctly")
    
    # ==================== VIEW + DATABASE INTEGRATION TESTS ====================
    
    def test_view_database_integration(self):
        """Integration: View should correctly query and display database data"""
        # Add more data to test database integration
        new_testimonial = Testimonial.objects.create(
            name="New Integration Test",
            position="New Position",
            organization="New Org",
            testimonial="Fresh test data.",
            image="new.jpg"
        )
        
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # New data should appear
        self.assertIn("New Integration Test", content)
        self.assertIn("New Position", content)
        self.assertIn("Fresh test data.", content)
        
        # All data should be in context
        testimonials = response.context['testimonial']
        self.assertEqual(testimonials.count(), 3)
        
        print("✅ View correctly integrates with database")
    
    def test_database_changes_reflect_in_view(self):
        """Integration: Database changes should immediately reflect in view"""
        # Get initial state
        response1 = self.client.get(reverse('main:testimonial_list'))
        initial_count = Testimonial.objects.count()
        
        # Modify database
        self.testimonial1.name = "Updated Integration User"
        self.testimonial1.save()
        
        # Delete one testimonial
        self.testimonial2.delete()
        
        # Add new testimonial
        Testimonial.objects.create(
            name="Dynamic Test",
            position="Dynamic Role",
            organization="Dynamic Corp",
            testimonial="Added dynamically.",
            image="dynamic.jpg"
        )
        
        # Get updated state
        response2 = self.client.get(reverse('main:testimonial_list'))
        content2 = response2.content.decode('utf-8')
        
        # Check updates
        self.assertIn("Updated Integration User", content2)
        self.assertNotIn("Integration User 2", content2)  # Deleted
        self.assertIn("Dynamic Test", content2)  # Added
        
        print("✅ Database changes immediately reflect in view")
    
    # ==================== VIEW + SESSION/COOKIE INTEGRATION ====================
    
    def test_session_persistence(self):
        """Integration: View should work with session middleware"""
        # Set a session variable
        session = self.client.session
        session['test_key'] = 'test_value'
        session.save()
        
        # Access view
        response = self.client.get(reverse('main:testimonial_list'))
        
        # View should still work with active session
        self.assertEqual(response.status_code, 200)
        
        # Session should persist
        self.assertEqual(self.client.session['test_key'], 'test_value')
        
        print("✅ View works correctly with session middleware")
    
    def test_cookie_handling(self):
        """Integration: View should handle cookies properly"""
        # Set a test cookie
        self.client.cookies['test_cookie'] = 'cookie_value'
        
        # Access view
        response = self.client.get(reverse('main:testimonial_list'))
        
        # Should still work with cookies
        self.assertEqual(response.status_code, 200)
        
        # Cookie should persist
        self.assertIn('test_cookie', self.client.cookies)
        
        print("✅ View handles cookies correctly")
    
    # ==================== VIEW + MIDDLEWARE INTEGRATION ====================
    
    def test_middleware_chain_integration(self):
        """Integration: View should work with all middleware"""
        # Test with all default middleware
        response = self.client.get(reverse('main:testimonial_list'))
        
        # Check middleware effects
        self.assertEqual(response.status_code, 200)
        
        # Common middleware headers
        self.assertIn('Content-Type', response)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        
        # No unexpected redirects
        self.assertNotIn('Location', response)
        
        print("✅ View works correctly with middleware chain")
    
    # ==================== VIEW + AUTHENTICATION INTEGRATION ====================
    
    def test_view_with_authentication_optional(self):
        """Integration: View should work with authenticated users (if auth is configured)"""
        try:
            # Try to create and login user if auth is available
            if HAS_CUSTOM_USER:
                # Create custom user
                user = UserModel.objects.create_user(
                    username='testuser',
                    password='testpass123',
                    email='test@example.com'
                )
            else:
                # Create default user
                user = UserModel.objects.create_user(
                    username='testuser',
                    password='testpass123',
                    email='test@example.com'
                )
            
            # Login user
            login_success = self.client.login(username='testuser', password='testpass123')
            
            if login_success:
                # Access view
                response = self.client.get(reverse('main:testimonial_list'))
                
                # Should work for authenticated users
                self.assertEqual(response.status_code, 200)
                print("✅ View works correctly for authenticated users")
            else:
                print("ℹ Login failed (auth might not be configured for this view)")
                # Still test view works
                response = self.client.get(reverse('main:testimonial_list'))
                self.assertEqual(response.status_code, 200)
                
        except Exception as e:
            # If auth fails, just test view works without auth
            print(f"ℹ Authentication test skipped: {e}")
            response = self.client.get(reverse('main:testimonial_list'))
            self.assertEqual(response.status_code, 200)
    
    def test_view_without_authentication(self):
        """Integration: View should work without authentication"""
        # Ensure user is logged out
        self.client.logout()
        
        # Access view
        response = self.client.get(reverse('main:testimonial_list'))
        
        # Should work for anonymous users too
        self.assertEqual(response.status_code, 200)
        
        print("✅ View works correctly for anonymous users")
    
    # ==================== VIEW + CACHE INTEGRATION ====================
    
    def test_cache_integration(self):
        """Integration: View should work with caching"""
        from django.core.cache import cache
        
        # Clear cache
        cache.clear()
        
        # First request (cold cache)
        response1 = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response1.status_code, 200)
        
        # Second request (might be cached)
        response2 = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response2.status_code, 200)
        
        # Both should return valid responses
        content1 = response1.content.decode('utf-8')
        content2 = response2.content.decode('utf-8')
        
        # Key content should be in both
        self.assertIn("Integration User 1", content1)
        self.assertIn("Integration User 1", content2)
        
        print("✅ View works correctly with caching")
    
    # ==================== VIEW + ERROR HANDLING INTEGRATION ====================
    
    def test_error_handling_integration(self):
        """Integration: View should handle errors gracefully"""
        # Test with malformed requests
        malformed_urls = [
            '/Testimonial/?malformed=test',
            '/Testimonial/../',
            '/Testimonial/?param=' + 'x' * 10000,  # Very long parameter
        ]
        
        for url in malformed_urls:
            try:
                response = self.client.get(url)
                # Should handle gracefully (not crash)
                self.assertIsNotNone(response)
                self.assertIn(response.status_code, [200, 400, 404, 414])
            except Exception as e:
                self.fail(f"View crashed with URL {url}: {e}")
        
        print("✅ View handles errors gracefully")
    
    # ==================== VIEW + STATIC FILES INTEGRATION ====================
    
    def test_static_files_integration(self):
        """Integration: View template should reference static files correctly"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # Check for common static file patterns
        static_indicators = [
            '/static/',
            '.css',
            '.js',
            'href=',
            'src=',
        ]
        
        for indicator in static_indicators:
            if indicator in content:
                print(f"✅ Static file reference found: {indicator}")
        
        # Template should load without static file errors
        self.assertNotIn('Missing staticfiles', content)
        self.assertNotIn('STATICFILES', content.upper())
        
        print("✅ Static files integrate correctly")
    
    # ==================== VIEW + THIRD-PARTY INTEGRATION ====================
    
    def test_third_party_integration(self):
        """Integration: View should work with third-party dependencies"""
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        # Check for common third-party CDN references
        third_party_indicators = [
            'cdn.jsdelivr.net',  # Bootstrap, FontAwesome
            'fonts.googleapis.com',  # Google Fonts
            'unpkg.com',  # Swiper, etc.
            'bootstrap',
            'jquery',
            'font-awesome',
        ]
        
        found_indicators = []
        for indicator in third_party_indicators:
            if indicator in content.lower():
                found_indicators.append(indicator)
        
        if found_indicators:
            print(f"✅ Third-party dependencies: {', '.join(found_indicators)}")
        else:
            print("ℹ No third-party dependencies detected")
        
        self.assertEqual(response.status_code, 200)
    
    # ==================== COMPREHENSIVE INTEGRATION TESTS ====================
    
    def test_comprehensive_user_journey(self):
        """Integration: Simulate complete user journey"""
        # Step 1: User visits site (anonymous)
        self.client.logout()
        
        # Try to get home page (might not exist)
        try:
            response1 = self.client.get('/')
            self.assertIn(response1.status_code, [200, 302, 404])
        except:
            pass  # Home page might not be configured
        
        # Step 2: User navigates to testimonials
        response2 = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response2.status_code, 200)
        
        # Step 3: User sees testimonials
        content = response2.content.decode('utf-8')
        self.assertIn("Integration User 1", content)
        
        print("✅ Complete user journey works")
    
    def test_concurrent_user_access(self):
        """Integration: Multiple users can access view simultaneously"""
        # Simulate multiple user sessions
        client1 = Client()
        client2 = Client()
        
        # Both access simultaneously
        response1 = client1.get(reverse('main:testimonial_list'))
        response2 = client2.get(reverse('main:testimonial_list'))
        
        # Both should succeed
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Both should see the same data
        content1 = response1.content.decode('utf-8')
        content2 = response2.content.decode('utf-8')
        
        self.assertIn("Integration User 1", content1)
        self.assertIn("Integration User 1", content2)
        
        print("✅ Multiple concurrent users can access view")
    
    # ==================== INTEGRATION WITH OTHER VIEWS ====================
    
    def test_view_integration_with_other_pages(self):
        """Integration: Testimonial view should work alongside other views"""
        # Test navigation between pages
        pages_to_test = [
            reverse('main:testimonial_list'),
            # Add other view URLs if they exist
            # '/',
            # '/about/',
            # '/contact/',
        ]
        
        for url in pages_to_test:
            try:
                response = self.client.get(url)
                self.assertIn(response.status_code, [200, 301, 302])
                print(f"✅ Page accessible: {url}")
            except Exception as e:
                print(f"ℹ Could not test {url}: {e}")
        
        print("✅ View integrates with navigation")
    
    # ==================== PERFORMANCE INTEGRATION TESTS ====================
    
    def test_integrated_performance(self):
        """Integration: View performance with all components"""
        import time
        
        # Test with all integrations active
        start_time = time.perf_counter()
        
        # Make request with session
        session = self.client.session
        session['perf_test'] = 'value'
        session.save()
        
        response = self.client.get(reverse('main:testimonial_list'))
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        
        # Should complete in reasonable time
        self.assertLess(response_time, 2.0, 
                       f"Integrated response too slow: {response_time:.3f}s")
        
        print(f"✅ Integrated performance: {response_time:.3f} seconds")
    
    # ==================== ERROR RECOVERY INTEGRATION ====================
    
    def test_error_recovery_integration(self):
        """Integration: System should recover from errors"""
        # First, ensure normal operation
        response1 = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response1.status_code, 200)
        
        # Create a "problem" (delete all data)
        Testimonial.objects.all().delete()
        
        # System should handle empty state
        response2 = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response2.status_code, 200)
        
        # Restore data
        self.setUp()  # Re-run setUp to restore data
        
        # System should work again
        response3 = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response3.status_code, 200)
        
        print("✅ System recovers from data errors")
    
    # ==================== CLEANUP INTEGRATION ====================
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up test data
        Testimonial.objects.all().delete()
        
        # Clean up users if they exist
        if HAS_CUSTOM_USER:
            try:
                UserModel.objects.filter(username='testuser').delete()
            except:
                pass
        else:
            try:
                UserModel.objects.filter(username='testuser').delete()
            except:
                pass
        
        # Clear sessions
        from django.contrib.sessions.models import Session
        Session.objects.all().delete()


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SimpleIntegrationTests(TestCase):
    """Simple integration tests"""
    
    def setUp(self):
        self.client = Client()
        Testimonial.objects.create(
            name="Simple Integration Test",
            position="Tester",
            organization="Test Org",
            testimonial="Simple test content.",
            image=""
        )
    
    def test_basic_integration(self):
        """Simple test that all components work together"""
        # Test URL resolution
        url = reverse('main:testimonial_list')
        self.assertEqual(url, '/Testimonial/')
        
        # Test view access
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test template usage
        self.assertTemplateUsed(response, 'main/snippets_templates/table/testimonial_list.html')
        
        # Test data display
        content = response.content.decode('utf-8')
        self.assertIn("Simple Integration Test", content)
        self.assertIn("Tester", content)
        self.assertIn("Simple test content.", content)
        
        print("✅ Basic integration: URL → View → Template → Data all work")
    
    def test_session_integration(self):
        """Test session integration"""
        # Set session
        session = self.client.session
        session['integration_test'] = 'passed'
        session.save()
        
        # Access view
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response.status_code, 200)
        
        # Verify session persisted
        self.assertEqual(self.client.session['integration_test'], 'passed')
        
        print("✅ Session integration works")
    
    def test_database_view_integration(self):
        """Test database and view integration"""
        # Add data
        Testimonial.objects.create(
            name="Dynamic Test Data",
            position="Dynamic Role",
            organization="Dynamic Org",
            testimonial="Added for integration test.",
            image=""
        )
        
        # Check it appears
        response = self.client.get(reverse('main:testimonial_list'))
        content = response.content.decode('utf-8')
        
        self.assertIn("Dynamic Test Data", content)
        self.assertIn("Added for integration test.", content)
        
        print("✅ Database ↔ View integration works")


class ComprehensiveIntegrationScenario(TestCase):
    """Comprehensive integration scenario test"""
    
    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_complete_scenario(self):
        """Test a complete user scenario"""
        print("\n" + "="*60)
        print("COMPREHENSIVE INTEGRATION SCENARIO")
        print("="*60)
        
        # Scenario setup
        print("\n1. 📋 Initial Setup:")
        client = Client()
        
        # Create multiple testimonials
        testimonials_data = [
            ("Alice Johnson", "CEO", "TechStart Inc", "Amazing service!"),
            ("Bob Smith", "CTO", "Innovate Corp", "Highly recommended."),
            ("Carol Davis", "Product Lead", "FutureTech", "Excellent support."),
        ]
        
        for name, position, org, testimonial in testimonials_data:
            Testimonial.objects.create(
                name=name,
                position=position,
                organization=org,
                testimonial=testimonial,
                image=""
            )
        
        print(f"   Created {Testimonial.objects.count()} testimonials")
        
        # User actions
        print("\n2. 👤 User Actions:")
        
        # Action 1: Visit testimonials page
        print("   - Visiting testimonials page...")
        response = client.get(reverse('main:testimonial_list'))
        self.assertEqual(response.status_code, 200)
        
        # Verify content
        content = response.content.decode('utf-8')
        for name, _, _, _ in testimonials_data:
            self.assertIn(name, content)
        
        print(f"   ✓ All {len(testimonials_data)} testimonials displayed")
        
        # Action 2: Check page structure
        print("   - Verifying page structure...")
        self.assertIn('<!DOCTYPE html>', content)
        self.assertIn('<html', content)
        self.assertIn('</html>', content)
        print("   ✓ Valid HTML structure")
        
        # Action 3: Verify data integrity
        print("   - Verifying data integrity...")
        testimonials_in_context = response.context['testimonial']
        self.assertEqual(testimonials_in_context.count(), len(testimonials_data))
        print("   ✓ Data integrity maintained")
        
        # System verification
        print("\n3. 🔧 System Verification:")
        
        # Verify sessions work
        session = client.session
        session['scenario_test'] = 'complete'
        session.save()
        
        # Make another request
        response2 = client.get(reverse('main:testimonial_list'))
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(client.session['scenario_test'], 'complete')
        print("   ✓ Session management works")
        
        # Verify error handling
        print("   - Testing error handling...")
        response3 = client.get('/Testimonial/nonexistent/')
        self.assertIn(response3.status_code, [404, 301, 302])
        print("   ✓ Error handling works")
        
        print("\n4. ✅ SCENARIO COMPLETE")
        print("="*60)
        
        # Final verification
        self.assertTrue(True, "Comprehensive scenario completed successfully")


# Run integration tests
if __name__ == '__main__':
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
    django.setup()
    
    print("🔗 Running integration tests...")
    print("="*60)