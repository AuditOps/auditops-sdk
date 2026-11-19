
# ==============================================================================
# ADMIN
# ==============================================================================

def collect_admin_evidence(collector):
    service = collector.service

    collect_m365_authentication(collector, service)
    collect_m365_roles(collector, service)
    collect_m365_users(collector, service)


# ==============================================================================
# AUTHENTICATION
# ==============================================================================

def collect_m365_authentication(collector, service):
    collector.collect(
        evidence_path="admin/authentication/mfa_registration.json",
        api_call=lambda: {
            "users": get_mfa_registration(service),
        },
    )


def get_mfa_registration(service):
    users = []
    url = (
        "https://graph.microsoft.com/v1.0/"
        "reports/authenticationMethods/userRegistrationDetails"
    )

    while url:
        response = service.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        users.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return users


# ==============================================================================
# ROLES
# ==============================================================================

def collect_m365_roles(collector, service):
    collector.collect(
        evidence_path="admin/roles.json",
        api_call=lambda: {
            "roles": get_roles(service),
        },
    )

    collector.collect(
        evidence_path="admin/role_assignments.json",
        api_call=lambda: {
            "role_assignments": get_role_assignments(service),
        },
    )


def get_roles(service):
    roles = []
    url = (
        "https://graph.microsoft.com/v1.0/"
        "roleManagement/directory/roleDefinitions"
    )

    while url:
        response = service.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        roles.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return roles


def get_role_assignments(service):
    role_assignments = []
    url = (
        "https://graph.microsoft.com/v1.0/"
        "roleManagement/directory/roleAssignments"
    )

    while url:
        response = service.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        role_assignments.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return role_assignments



# ==============================================================================
# USERS
# ==============================================================================

def collect_m365_users(collector, service):
    collector.collect(
        evidence_path="admin/users.json",
        api_call=lambda: {
            "users": get_users(service),
        },
    )


def get_users(service):
    users = []
    url = (
        "https://graph.microsoft.com/v1.0/"
        "users?$select=id,displayName,userPrincipalName,mail,"
        "accountEnabled,userType,signInActivity,createdDateTime"
    )

    while url:
        response = service.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        users.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return users
