package workspaces

import (
	"testing"
)

func TestRoleHierarchy(t *testing.T) {
	order := []string{RoleViewer, RoleMember, RoleWorkspaceOwner, RoleOrgOwner, RoleAdmin}
	for i, role := range order {
		if RoleLevel(role) <= 0 {
			t.Fatalf("role %q must have positive level", role)
		}
		if i > 0 && RoleLevel(role) <= RoleLevel(order[i-1]) {
			t.Fatalf("role %q must outrank %q", role, order[i-1])
		}
	}
	if RoleLevel("bogus") != -1 {
		t.Fatal("unknown role must be -1")
	}
}

func TestRoleAtLeast(t *testing.T) {
	cases := []struct {
		have, want string
		ok         bool
	}{
		{RoleWorkspaceOwner, RoleMember, true},
		{RoleMember, RoleWorkspaceOwner, false},
		{RoleViewer, RoleViewer, true},
		{RoleOrgOwner, RoleWorkspaceOwner, true},
		{RoleAdmin, RoleOrgOwner, true},
		{"bogus", RoleViewer, false},
	}
	for _, c := range cases {
		if got := RoleAtLeast(c.have, c.want); got != c.ok {
			t.Errorf("RoleAtLeast(%q,%q) = %v, want %v", c.have, c.want, got, c.ok)
		}
	}
}
