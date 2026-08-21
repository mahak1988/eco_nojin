import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "@/lib/api-client";

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("uses the configured base URL and attaches the auth token", async () => {
    localStorage.setItem("auth_token", "test-token");
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ status: "operational" }), { status: 200 })
    );

    const result = await api.get<{ status: string }>("/api/v1/health");

    expect(result).toEqual({
      success: true,
      data: { status: "operational" },
      status: 200,
    });
    expect(fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/health$/),
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          Authorization: "Bearer test-token",
          "Content-Type": "application/json",
        }),
      })
    );
  });

  it("normalizes API errors and clears expired auth", async () => {
    localStorage.setItem("auth_token", "expired-token");
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ detail: "Authentication required" }), { status: 401 })
    );

    const result = await api.get("/api/v1/farms/");

    expect(result).toEqual({
      success: false,
      error: "Authentication required",
      status: 401,
    });
    expect(localStorage.getItem("auth_token")).toBeNull();
  });
});