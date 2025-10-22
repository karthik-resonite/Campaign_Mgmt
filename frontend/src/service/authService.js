// services/authService.js
import axios from "axios";

const API_URL = "https://redsocks.mu:9000"; // adjust if needed

export const RegistorUser = async (c_name, username, email, phone, password) => {
  try {
    const response = await axios.post(`${API_URL}/companies/`, {
      name: c_name,
      username,
      email,
      phone,
      password
    }, {
      headers: {
        "Content-Type": "application/json"
      }
    });

    return response.data;
  } catch (error) {
    throw error.response?.data || { detail: "Registration failed" };
  }
};

export const loginUser = async (username, password) => {
  try {
    // FastAPI expects application/x-www-form-urlencoded
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);

    const response = await axios.post(`${API_URL}/auth/login`, params, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      }
    });

    return response.data; // { access_token, token_type }
  } catch (error) {
    throw error.response?.data || { detail: "Login failed" };
  }
};

export const changePassword = async (username, oldPassword, newPassword, token) => {
  return axios.post(
    `${API_URL}/auth/change-password`,
    {
      username,
      old_password: oldPassword,
      new_password: newPassword,
    },
    {
      headers: {
        Authorization: `Bearer ${token}`, // ✅ add bearer token here
      },
    }
  );
};

// export const changePassword = async (oldPassword, newPassword, token) => {
//   try {
//     const response = await axios.post(
//       `${API_URL}/auth/change-password`,
//       { old_password: oldPassword, new_password: newPassword },
//       {
//         headers: {
//           Authorization: `Bearer ${token}`
//         }
//       }
//     );
//     return response.data;
//   } catch (error) {
//     throw error.response?.data || { detail: "Change password failed" };
//   }
// };

export const forgotPassword = async (username) => {
  return axios.post(`${API_URL}/auth/forgot-password`, null, {
    params: { username }
  });
};

export const verify_otp = async (payload) => {
  return axios.post(`${API_URL}/auth/verify-otp`, payload, {
    headers: { "Content-Type": "application/json" }
  });
};

export const resetPassword = async (username, newPassword) => {
  return axios.post(`${API_URL}/auth/reset-password`, {
    username,
    new_password: newPassword,
  });
};