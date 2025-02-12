from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from rolepermissions.checkers import has_permission

class HasPermission(BasePermission):
	"""
		This is a custom permission class for DRF that checks if the user 
		has the required permission.
		Usage in drf views:
		permission_classes = [HasPermission]
		permission_required = PERM_MODIFY_SCAN_CONFIGURATIONS
	"""

	def has_permission(self, request, view):
		"""
		Determine whether the request user has the required permission to access the view.
		
		This method retrieves the permission code from the view's `permission_required` attribute.
		If the attribute is not set, it raises a PermissionDenied exception indicating that the
		required permission is not specified. If the permission code is provided, the method
		checks whether the user has the specified permission using the appropriate permission checker.
		If the user does not have the required permission, a PermissionDenied exception is raised.
		On success, it returns True, granting access to the view.
		
		Parameters:
		    request (HttpRequest): The HTTP request object containing the user instance.
		    view (View): The view being accessed, expected to have a `permission_required` attribute.
		
		Returns:
		    bool: True if the user has the required permission.
		
		Raises:
		    PermissionDenied: If the view does not specify a permission or if the user lacks the required permission.
		"""
		permission_code = getattr(view, 'permission_required', None)
		if not permission_code:
			raise PermissionDenied(detail="Permission is not specified for this view.")

		if not has_permission(request.user, permission_code):
			raise PermissionDenied(detail="This user does not have enough permissions")
		return True
