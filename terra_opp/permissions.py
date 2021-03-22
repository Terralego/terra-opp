from rest_framework.permissions import SAFE_METHODS, BasePermission


class ViewpointPermission(BasePermission):
    """ Read only for anonymous users or has terra permission """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return not request.user.is_anonymous and request.user.has_terra_perm(
            "can_manage_viewpoints"
        )


class CampaignPermission(BasePermission):
    """ Read only for authenticated users or has terra permission """

    def has_permission(self, request, view):

        if request.user.is_anonymous:
            return False

        if request.method in SAFE_METHODS:
            return request.user.has_terra_perm(
                "can_add_pictures"
            ) or request.user.has_terra_perm("can_manage_campaigns")

        return request.user.has_terra_perm("can_manage_campaigns")

    def has_object_permission(self, request, view, obj):
        """
        User with permission can_add_pictures can only
        modify assigned campaings
        """
        if request.method in SAFE_METHODS:
            if request.user.has_terra_perm("can_manage_campaigns"):
                return True
            elif request.user.has_terra_perm("can_add_pictures"):
                return obj.assignee == request.user

        return request.user.has_terra_perm("can_manage_campaigns")


class PicturePermission(BasePermission):
    """ Read only for anonymous users or has terra permissions """

    def has_permission(self, request, view):

        if request.method in SAFE_METHODS:
            return True

        if request.user.is_anonymous:
            return False

        if request.user.has_terra_perm("can_manage_pictures"):
            return True

        if request.user.has_terra_perm("can_add_pictures"):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        """
        User with permission can_add_pictures can only
        modify self picture in state DRAFT or REFUSED
        """
        if request.method in SAFE_METHODS:
            return True

        if request.user.has_terra_perm("can_manage_pictures"):
            return True

        if request.user.has_terra_perm("can_add_pictures"):
            return obj.owner == request.user and obj.state in [
                "draft",
                "refused",
            ]

        return False
