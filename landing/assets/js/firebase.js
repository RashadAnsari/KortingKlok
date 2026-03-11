import { initializeApp } from "https://www.gstatic.com/firebasejs/12.10.0/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/12.10.0/firebase-analytics.js";

const firebaseConfig = {
  apiKey: "AIzaSyDlyyr16sAFtu60FRYPbRpLU6EuI5AdGdY",
  authDomain: "kortingklok.firebaseapp.com",
  projectId: "kortingklok",
  storageBucket: "kortingklok.firebasestorage.app",
  messagingSenderId: "227043916405",
  appId: "1:227043916405:web:0f4a6d571309fdeedcd63c",
  measurementId: "G-1LYJD5CSZ2"
};

const app = initializeApp(firebaseConfig);

window._activateFirebaseAnalytics = function() {
  getAnalytics(app);
};

if (window._kkAnalyticsConsented) {
  window._activateFirebaseAnalytics();
}
