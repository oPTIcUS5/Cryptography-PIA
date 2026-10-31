/* Demostracion con RSA-OAEP + AES-256-GCM*/

"use strict";
const encoder = new TextEncoder();

function fromBase64(text) {

    const binary = atob(text);
    const bytes = new Uint8Array(binary.length);

    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }

    return bytes;
}


function toBase64(bytes) {

    let binary = "";

    for (const byte of new Uint8Array(bytes)) {
        binary += String.fromCharCode(byte)
    }

    return btoa(binary);
}


async function encryptvote(election, candidate) {
    
    if(!crypto?.subtle || !crypto?.getRandomValues) {
        throw new Error("Navegador sin web crypto API. Usa https o localhost")
    }

    if (!Object.hasOwn(election.candidates, candidate)) {
        throw new Error("Candidatura inválida");
    }

    const rsaPublic = await crypto.subtle.importKey(
        "spki", fromBase64(election.public_key_spki_base64),
        {name: "RSA-OAEP", hash: "SHA-256"}, false, ["encrypt"]
    );

    const aes = await crypto.subtle.generateKey(
        {name: "AES-GCM", length: 256}, true, ["encrypt"]
    );

    const nonce = crypto.getRandomValues(new Uint8Array(12));

    const data = encoder.encode(JSON.stringify({
        election_id: election.election_id, candidate_id: candidate
    }));

    const ciphertext = await crypto.subtle.encrypt(
        {name: "AES-GCM", iv: nonce, additionalData: encoder.encode(election.election_id), tagLength: 128},
        aes, data
    );

    const aesRaw = await crypto.subtle.exportKey("raw", aes);
    const wrappedKey = await crypto.subtle.encrypt({name: "RSA-OAEP"}, rsaPublic, aesRaw);
    
    return {wrapped_key: toBase64(wrappedKey), nonce: toBase64(nonce), ciphertext: toBase64(ciphertext)};
}

const form = document.querySelector("#vote-form");
if (form) form.addEventListener("submit", async event => {
    event.preventDefault();
    const button = document.querySelector("#submit-vote");
    const feedback = document.querySelector("#feedback");
    const selection = new FormData(form).get("candidate");

    if (!selection) return;
    button.disabled = true;
    feedback.textContent = "Cifrando y registrando…";

    try {
        const confResponse = await fetch("/api/config", {cache: "no-store"});

        if (!confResponse.ok) throw new Error("No fue posible obtener la clave pública");
        const election = await confResponse.json();

        if (election.status !== "open") throw new Error("La elección está cerrada");

        const payload = await encryptVote(election, selection);

        const response = await fetch("/api/vote", {
        method: "POST", credentials: "same-origin",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content},
        body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "No fue posible registrar el voto");
        
        // No presentar la selección como comprobante público.
        window.location.assign(result.verification_url);
    } catch (error) {
        feedback.textContent = `Error: ${error.message}`;
        button.disabled = false;
    }
});
