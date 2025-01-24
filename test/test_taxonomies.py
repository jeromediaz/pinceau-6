from misc.taxonomy import TaxonomyPermissions, Permission, get_rights


def test_taxonomies():

    permissions = [
        TaxonomyPermissions(taxonomy="/", can_read=Permission.allowed),
        TaxonomyPermissions(taxonomy="/system/", can_read=Permission.allowed),
        TaxonomyPermissions(taxonomy="/system/a/b/", can_read=Permission.allowed),
    ]

    rights = get_rights("/system/a/", permissions)



    print(rights)
