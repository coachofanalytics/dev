"""
Generic mixins for CODA application to reduce code duplication
and standardize common functionality across views.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
from django.views.generic import ListView


class FilteredListViewMixin:
    """Generic mixin for filtered list views to eliminate duplication"""

    model = None
    filter_fields = []
    order_by = "-date_joined"
    template_name = None
    paginate_by = 20

    def get_queryset(self):
        """Apply common filtering logic"""
        queryset = self.model.objects.all()

        # Apply category filters if defined
        if hasattr(self, "category_filters"):
            for category, subcategory in self.category_filters.items():
                if subcategory:
                    queryset = queryset.filter(
                        category=category, sub_category=subcategory
                    )
                else:
                    queryset = queryset.filter(category=category)

        # Apply active filter
        if (
            self.request.GET.get("active_only")
            and hasattr(self.model, "_meta")
            and "is_active" in [f.name for f in self.model._meta.fields]
        ):
            queryset = queryset.filter(is_active=True)

        # Apply search if model has search_fields
        search_query = self.request.GET.get("search")
        if search_query and hasattr(self.model, "search_fields"):
            q_objects = Q()
            for field in self.model.search_fields:
                q_objects |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(q_objects)

        return queryset.order_by(self.order_by)

    def get_context_data(self, **kwargs):
        """Add common context data"""
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context["total_count"] = queryset.count()

        # Only filter by is_active if the field exists
        if hasattr(self.model, "_meta") and "is_active" in [
            f.name for f in self.model._meta.fields
        ]:
            context["active_count"] = queryset.filter(is_active=True).count()
        else:
            context["active_count"] = queryset.count()

        return context


class CODAObjectMixin:
    """Base mixin for CODA objects with common functionality"""

    def get_context_data(self, **kwargs):
        """Add common context data"""
        context = super().get_context_data(**kwargs)
        if hasattr(self, "model") and self.model:
            context["app_name"] = self.model._meta.app_label
            context["model_name"] = self.model._meta.verbose_name
        return context

    def handle_form_valid(self, form):
        """Centralized form validation logic"""
        try:
            response = super().form_valid(form)
            if hasattr(self, "model") and self.model:
                messages.success(
                    self.request, f"{self.model._meta.verbose_name} saved successfully."
                )
            else:
                messages.success(self.request, "Item saved successfully.")
            return response
        except Exception as e:
            if hasattr(self, "model") and self.model:
                messages.error(
                    self.request,
                    f"Error saving {self.model._meta.verbose_name}: {str(e)}",
                )
            else:
                messages.error(self.request, f"Error saving item: {str(e)}")
            return self.form_invalid(form)


class CODAListView(CODAObjectMixin, ListView):
    """Generic list view with common functionality"""

    paginate_by = 20
    ordering = ["-created_at"]

    def get_queryset(self):
        """Apply common filters and search"""
        queryset = super().get_queryset()

        # Apply common filters
        if (
            self.request.GET.get("active_only")
            and hasattr(self.model, "_meta")
            and "is_active" in [f.name for f in self.model._meta.fields]
        ):
            queryset = queryset.filter(is_active=True)

        # Apply search
        search_query = self.request.GET.get("search")
        if search_query and hasattr(self.model, "search_fields"):
            q_objects = Q()
            for field in self.model.search_fields:
                q_objects |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(q_objects)

        return queryset.order_by(self.ordering)


class CODAPermissionMixin:
    """Centralized permission checking for CODA views"""

    required_permissions = []
    required_category = None
    required_subcategory = None
    permission_denied_message = "You don't have permission to access this page."
    permission_denied_redirect = "main:layout"

    def has_permission(self):
        """Centralized permission checking"""
        user = self.request.user

        # Check Django permissions
        if self.required_permissions:
            if not user.has_perms(self.required_permissions):
                return False

        # Check category requirements
        if self.required_category:
            if user.category != self.required_category:
                return False

        # Check subcategory requirements
        if self.required_subcategory:
            if user.sub_category != self.required_subcategory:
                return False

        return True

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before dispatching"""
        if not self.has_permission():
            messages.error(request, self.permission_denied_message)
            return redirect(self.permission_denied_redirect)
        return super().dispatch(request, *args, **kwargs)


class UserCategoryMixin:
    """Mixin for views that need to filter by user category"""

    def get_queryset(self):
        """Filter queryset by user category if specified"""
        queryset = super().get_queryset()

        if hasattr(self, "user_category_filter"):
            user = self.request.user
            if user.category == self.user_category_filter:
                return queryset
            else:
                return self.model.objects.none()

        return queryset


class SuccessMessageMixin:
    """Mixin for consistent success messages"""

    success_message = None

    def get_success_message(self):
        """Get the success message to display"""
        if self.success_message:
            return self.success_message
        elif hasattr(self, "model") and self.model:
            return f"{self.model._meta.verbose_name} saved successfully."
        return "Item saved successfully."

    def form_valid(self, form):
        """Add success message on form validation"""
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message())
        return response
