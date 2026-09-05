package auth

import (
	"testing"
	"time"
)

func TestHashAndVerifyPassword(t *testing.T) {
	hash, err := HashPassword("correct horse battery")
	if err != nil {
		t.Fatal(err)
	}
	if hash == "correct horse battery" {
		t.Fatal("hash must not equal plaintext")
	}
	if !VerifyPassword(hash, "correct horse battery") {
		t.Fatal("correct password must verify")
	}
	if VerifyPassword(hash, "wrong password here") {
		t.Fatal("wrong password must not verify")
	}
}

func TestHashRejectsShortPassword(t *testing.T) {
	if _, err := HashPassword("short"); err == nil {
		t.Fatal("expected error for password under 8 characters")
	}
}

func TestIssueAndParseTokenRoundtrip(t *testing.T) {
	token, err := IssueToken("secret-at-least-32-bytes-long!!", "user-1", "a@b.c", "admin", time.Hour)
	if err != nil {
		t.Fatal(err)
	}
	claims, err := ParseToken("secret-at-least-32-bytes-long!!", token)
	if err != nil {
		t.Fatal(err)
	}
	if claims.UserID != "user-1" || claims.Email != "a@b.c" || claims.Role != "admin" {
		t.Fatalf("claims mismatch: %+v", claims)
	}
}

func TestParseTokenWrongSecret(t *testing.T) {
	token, _ := IssueToken("secret-at-least-32-bytes-long!!", "u", "a@b.c", "member", time.Hour)
	if _, err := ParseToken("another-secret-32-bytes-long!!!!!!", token); err == nil {
		t.Fatal("expected error with wrong secret")
	}
}

func TestParseTokenExpired(t *testing.T) {
	token, _ := IssueToken("secret-at-least-32-bytes-long!!", "u", "a@b.c", "member", -time.Minute)
	if _, err := ParseToken("secret-at-least-32-bytes-long!!", token); err == nil {
		t.Fatal("expected error for expired token")
	}
}

func TestParseTokenTampered(t *testing.T) {
	token, _ := IssueToken("secret-at-least-32-bytes-long!!", "u", "a@b.c", "member", time.Hour)
	if _, err := ParseToken("secret-at-least-32-bytes-long!!", token+"x"); err == nil {
		t.Fatal("expected error for tampered token")
	}
}

func TestIssueTokenEmptySecret(t *testing.T) {
	if _, err := IssueToken("", "u", "a@b.c", "member", time.Hour); err == nil {
		t.Fatal("expected error for empty secret")
	}
}
