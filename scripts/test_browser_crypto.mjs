// Simula con Node la misma Web Crypto API que utiliza un navegador moderno.
// Uso: node scripts/test_browser_crypto.mjs data/encryption_public.pem A

import { readFileSync } from "node:fs";
import { webcrypto } from "node:crypto";
const { subtle } = webcrypto;

const publicPem = readFileSync(process.argv[2], "utf8");
const candidateId = process.argv[3] ?? "A";
const electionId = "MUNICIPAL-DEMO-2026";

const der = Buffer.from(publicPem.replace(/-----[^-]+-----/g, "").replace(/\s+/g, ""), "base64");

const rsa = await subtle.importKey("spki", der, {name:"RSA-OAEP",hash:"SHA-256"},false,["encrypt"]);
const aes = await subtle.generateKey({name:"AES-GCM",length:256},true,["encrypt"]);

const nonce = webcrypto.getRandomValues(new Uint8Array(12));

const utf8 = new TextEncoder();
const bytes = utf8.encode(JSON.stringify({election_id:electionId,candidate_id:candidateId}));

const ciphertext = await subtle.encrypt({name:"AES-GCM", iv:nonce,
    additionalData:utf8.encode(electionId),tagLength:128}, aes, bytes);

const raw = await subtle.exportKey("raw",aes);
const wrapped = await subtle.encrypt({name:"RSA-OAEP"},rsa,raw);

console.log(JSON.stringify({wrapped_key:Buffer.from(wrapped).toString("base64"),
    nonce:Buffer.from(nonce).toString("base64"),
    ciphertext:Buffer.from(ciphertext).toString("base64")}));
