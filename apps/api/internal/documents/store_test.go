package documents

import (
	"context"
	"errors"
	"io"
	"strings"
	"testing"
)

type fakeStorage struct {
	objects map[string][]byte
}

func (f *fakeStorage) PutObject(_ context.Context, key string, r io.Reader, _ int64, _ string) error {
	if f.objects == nil {
		f.objects = map[string][]byte{}
	}
	b, err := io.ReadAll(r)
	if err != nil {
		return err
	}
	f.objects[key] = b
	return nil
}

func TestSanitizeFilename(t *testing.T) {
	cases := map[string]string{
		"../../etc/passwd":  "passwd",
		"report final.pdf":  "report final.pdf",
		"weird/name\\x?.md": "name_x_.md",
		"":                  "upload",
		"..":                "upload",
	}
	for in, want := range cases {
		if got := sanitizeFilename(in); got != want {
			t.Errorf("sanitizeFilename(%q) = %q, want %q", in, got, want)
		}
	}
}

func TestAllowedContentTypes(t *testing.T) {
	for _, ct := range []string{
		"application/pdf", "text/plain", "text/markdown", "text/csv",
		"image/png", "image/jpeg",
	} {
		if _, ok := AllowedContentTypes[ct]; !ok {
			t.Errorf("expected %q to be allowed", ct)
		}
	}
	if _, ok := AllowedContentTypes["application/x-msdownload"]; ok {
		t.Error("executables must not be allowed")
	}
}

func TestObjectKeyIsUUIDBased(t *testing.T) {
	key := ObjectKey("abc-123", ".pdf")
	if key != "documents/abc-123.pdf" {
		t.Fatalf("key = %q", key)
	}
	if strings.Contains(key, "..") {
		t.Fatal("object keys must never allow traversal")
	}
}

func TestFakeStorageRoundtrip(t *testing.T) {
	fs := &fakeStorage{}
	if err := fs.PutObject(context.Background(), "k", strings.NewReader("hello"), 5, "text/plain"); err != nil {
		t.Fatal(err)
	}
	if string(fs.objects["k"]) != "hello" {
		t.Fatalf("stored %q", fs.objects["k"])
	}
}

func TestErrorSentinels(t *testing.T) {
	if !errors.Is(ErrUnsupportedType, ErrUnsupportedType) || !errors.Is(ErrNotFound, ErrNotFound) {
		t.Fatal("sentinels must be usable with errors.Is")
	}
}
