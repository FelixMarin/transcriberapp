/**
 * Tests para el módulo utils.js
 * @jest-environment jsdom
 */

import {
    formatAsHTML,
    generateId,
    isValidEmail,
    isValidName,
    normalizeText,
    parseMarkdown
} from "../utils.js";

describe("utils.js", () => {

    describe("generateId", () => {
        it("debe generar un ID único basado en nombre y fecha", async () => {
            const id1 = await generateId("test", "2024-01-01");
            const id2 = await generateId("test", "2024-01-02");

            expect(id1).not.toBe(id2);
            expect(id1).toMatch(/^[a-f0-9]{64}$/); // SHA-256 hex
        });
    });

    describe("formatAsHTML", () => {
        it("debe escapar caracteres HTML peligrosos", () => {
            const result = formatAsHTML("<script>alert('xss')</script>");
            expect(result).toContain("&lt;script&gt;");
            expect(result).not.toContain("<script>");
        });

        it("debe convertir saltos de línea a <br>", () => {
            const result = formatAsHTML("línea1\nlínea2");
            expect(result).toContain("<br>");
        });

        it("debe devolver string vacío para entrada vacía", () => {
            expect(formatAsHTML("")).toBe("");
            expect(formatAsHTML(null)).toBe("");
        });
    });

    describe("parseMarkdown", () => {
        it("debe retornar string vacío para entrada vacía", () => {
            expect(parseMarkdown("")).toBe("");
            expect(parseMarkdown(null)).toBe("");
        });

        it("debe devolver <pre> si marked no está disponible", () => {
            const original = global.marked;
            global.marked = undefined;

            const result = parseMarkdown("# Título");
            expect(result).toContain("<pre>");

            global.marked = original;
        });
    });

    describe("normalizeText", () => {
        it("debe convertir a minúsculas", () => {
            expect(normalizeText("HOLA")).toBe("hola");
            expect(normalizeText("MiXtO")).toBe("mixto");
        });

        it("debe remover acentos", () => {
            expect(normalizeText("José")).toBe("jose");
            expect(normalizeText("García")).toBe("garcia");
            expect(normalizeText("Mañana")).toBe("manana");
        });
    });

    describe("isValidEmail", () => {
        it("debe validar emails correctos", () => {
            expect(isValidEmail("user@example.com")).toBe(true);
            expect(isValidEmail("test.email@domain.co.uk")).toBe(true);
        });

        it("debe rechazar emails sin @", () => {
            expect(isValidEmail("useremail.com")).toBe(false);
        });

        it("debe rechazar emails sin punto", () => {
            expect(isValidEmail("user@com")).toBe(false);
        });

        it("debe rechazar emails vacíos", () => {
            expect(isValidEmail("")).toBe(false);
        });
    });

    describe("isValidName", () => {
        it("debe aceptar nombres con al menos 5 caracteres", () => {
            expect(isValidName("María")).toBe(true);
            expect(isValidName("Juan Carlos")).toBe(true);
        });

        it("debe rechazar nombres con menos de 5 caracteres", () => {
            expect(isValidName("Juan")).toBe(false);
            expect(isValidName("Ana")).toBe(false);
        });

        it("debe ignorar espacios al inicio/final", () => {
            expect(isValidName("  María  ")).toBe(true);
            expect(isValidName("  Juan  ")).toBe(false);
        });
    });
});
