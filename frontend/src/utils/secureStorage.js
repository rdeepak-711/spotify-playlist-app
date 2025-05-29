// Get encryption key from environment variables
const ENCRYPTION_KEY = import.meta.env.VITE_ENCRYPTION_KEY;

if (!ENCRYPTION_KEY || ENCRYPTION_KEY.length < 32) {
  console.error("Invalid encryption key. Must be at least 32 characters long");
}

const generateIV = () => {
  return crypto.getRandomValues(new Uint8Array(12));
};

const encryptData = async (data) => {
  try {
    // Convert the encryption key to a CryptoKey object
    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(ENCRYPTION_KEY),
      { name: "AES-GCM" },
      false,
      ["encrypt"]
    );

    // Generate a random IV for this encryption
    const iv = generateIV();

    // Convert data to bytes
    const encodedData = new TextEncoder().encode(JSON.stringify(data));

    // Encrypt the data using AES-GCM
    const encryptedData = await crypto.subtle.encrypt(
      {
        name: "AES-GCM",
        iv: iv,
      },
      key,
      encodedData
    );

    // Combine IV and encrypted data for storage
    // We need to store the IV with the data to decrypt it later
    const encryptedArray = new Uint8Array(iv.length + encryptedData.byteLength);
    encryptedArray.set(iv);
    encryptedArray.set(new Uint8Array(encryptedData), iv.length);

    // Convert to base64 for storage
    return btoa(String.fromCharCode(...encryptedArray));
  } catch (e) {
    console.error("Encryption error:", e);
    return null;
  }
};

const decryptData = async (encrypted) => {
  try {
    // Convert base64 back to bytes
    const encryptedArray = new Uint8Array(
      atob(encrypted)
        .split("")
        .map((char) => char.charCodeAt(0))
    );

    // Extract the IV and data
    const iv = encryptedArray.slice(0, 12);
    const data = encryptedArray.slice(12);

    // Import the encryption key
    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(ENCRYPTION_KEY),
      { name: "AES-GCM" },
      false,
      ["decrypt"]
    );

    // Decrypt the data
    const decryptedData = await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: iv,
      },
      key,
      data
    );

    // Convert decrypted data back to object
    return JSON.parse(new TextDecoder().decode(decryptedData));
  } catch (e) {
    console.error("Decryption error:", e);
    return null;
  }
};

// Key used in localStorage
const AUTH_STORAGE_KEY = "spotify_auth_data";

// Token expiration time (1 hour)
const TOKEN_EXPIRY_TIME = 3600 * 1000;

export const saveAuthData = async (data) => {
  const dataWithTimestamp = {
    ...data,
    timestamp: Date.now(),
  };

  const encrypted = await encryptData(dataWithTimestamp);
  if (encrypted) {
    localStorage.setItem(AUTH_STORAGE_KEY, encrypted);
    return true;
  }
  return false;
};

export const getAuthData = async () => {
  const encrypted = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!encrypted) return null;

  const decrypted = await decryptData(encrypted);
  if (!decrypted) return null;

  // Check if token has expired
  const now = Date.now();
  if (now - decrypted.timestamp > TOKEN_EXPIRY_TIME) {
    clearAuthData();
    return null;
  }

  return decrypted;
};

export const clearAuthData = () => {
  localStorage.removeItem(AUTH_STORAGE_KEY);
};

export const isTokenExpired = async (token) => {
  if (!token) return true;

  try {
    const authData = await getAuthData();
    if (!authData) return true;

    const now = Date.now();
    return now - authData.timestamp > TOKEN_EXPIRY_TIME;
  } catch (e) {
    console.error("Token validation error:", e);
    return true;
  }
};
