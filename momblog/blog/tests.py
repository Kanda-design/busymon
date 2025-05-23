from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Post, Category
from .forms import PostForm

# Create your tests here.

class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Test Category")

    def test_category_str(self):
        self.assertEqual(str(self.category), "Test Category")

class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(name="Test Category")
        self.post = Post.objects.create(
            title="Test Post Title",
            content="Test Post Content.",
            author=self.user,
            category=self.category
        )

    def test_post_creation(self):
        self.assertEqual(self.post.title, "Test Post Title")
        self.assertEqual(self.post.content, "Test Post Content.")
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.category, self.category)
        self.assertTrue(Post.objects.exists())

    def test_post_str(self):
        self.assertEqual(str(self.post), "Test Post Title")

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.category = Category.objects.create(name="Test Category")
        self.post1 = Post.objects.create(
            title="Post by User1",
            content="Content by User1.",
            author=self.user1,
            category=self.category
        )

    def test_post_list_view_no_posts(self):
        Post.objects.all().delete() # Ensure no posts exist
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No posts have been published yet.")

    def test_post_list_view_with_posts(self):
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post1.title)
        self.assertNotContains(response, "No posts have been published yet.")

    def test_post_detail_view(self):
        response = self.client.get(reverse('post_detail', args=[self.post1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post1.title)
        self.assertContains(response, self.post1.content)

    # CRUD View Access Tests
    def test_post_create_view_unauthenticated(self):
        response = self.client.get(reverse('post_create'))
        self.assertEqual(response.status_code, 302) # Redirects to login
        self.assertIn(reverse('login'), response.url)

    def test_post_create_view_authenticated(self):
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('post_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create New Post")

    # PostUpdateView Tests
    def test_post_update_view_unauthenticated(self):
        response = self.client.get(reverse('post_update', args=[self.post1.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_post_update_view_wrong_user(self):
        self.client.login(username='user2', password='password123')
        response = self.client.get(reverse('post_update', args=[self.post1.pk]))
        self.assertEqual(response.status_code, 403) # Forbidden

    def test_post_update_view_correct_user(self):
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('post_update', args=[self.post1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Post")
        self.assertContains(response, self.post1.title)

    # PostDeleteView Tests
    def test_post_delete_view_unauthenticated(self):
        response = self.client.get(reverse('post_delete', args=[self.post1.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_post_delete_view_wrong_user(self):
        self.client.login(username='user2', password='password123')
        response = self.client.get(reverse('post_delete', args=[self.post1.pk]))
        self.assertEqual(response.status_code, 403) # Forbidden

    def test_post_delete_view_correct_user(self):
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('post_delete', args=[self.post1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Are you sure you want to delete \"{self.post1.title}\"?")


class PostFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='formuser', password='password123')
        self.category = Category.objects.create(name="Form Test Category")

    def test_post_form_valid(self):
        form_data = {
            'title': 'Valid Title',
            'content': 'Valid content for the post.',
            'category': self.category.pk
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors.as_json()}")

    def test_post_form_invalid_missing_title(self):
        form_data = {
            'title': '', # Missing title
            'content': 'Some content.',
            'category': self.category.pk
        }
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_post_form_invalid_missing_content(self):
        form_data = {
            'title': 'A Title',
            'content': '', # Missing content
            'category': self.category.pk
        }
        form = PostForm(data=form_data)
        # Content is not strictly required by the model (TextField can be blank)
        # but if it were, this test would be:
        # self.assertFalse(form.is_valid())
        # self.assertIn('content', form.errors)
        # For now, let's assume the form doesn't add extra validation for content being non-empty beyond the model
        # If the model had blank=False for content, then this would be an invalid form.
        # Let's check the model definition.
        # Post model has content = models.TextField() - default is blank=False, null=False
        # So, an empty content string should make the form invalid.
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)


    def test_post_form_category_optional(self):
        form_data = {
            'title': 'Title without Category',
            'content': 'Content without category.'
            # 'category' is not provided
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors.as_json()}")
        # Check that a post can be created without a category
        if form.is_valid():
            post = form.save(commit=False)
            post.author = self.user
            post.save()
            self.assertIsNone(post.category)
            self.assertEqual(Post.objects.count(), 1)
            Post.objects.all().delete() # Clean up for other tests
        else:
            self.fail(f"Form should be valid without category. Errors: {form.errors.as_json()}")
