import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyAzkRBn5gb2DLExvNfpsfO1lU-BGBzXy2Q",
  authDomain: "ripple-production-intelligence.firebaseapp.com",
  projectId: "ripple-production-intelligence",
  storageBucket: "ripple-production-intelligence.firebasestorage.app",
  messagingSenderId: "357403162742",
  appId: "1:357403162742:web:31fcc21d1687a5fd1e0757",
  measurementId: "G-NDBE3Q8196",
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);