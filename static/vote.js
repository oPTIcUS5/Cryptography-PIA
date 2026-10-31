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
}
