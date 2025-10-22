// services/campaignservice.js
import axios from "axios";

const API_URL = "https://redsocks.mu:9000"; // adjust if needed

const ELEVEN_API = "https://api.elevenlabs.io/v1/convai";
const API_KEY = "sk_3c2a89de0706aa7b4b08fcad0764b3fa14448e143d396301";

export const create_Campaign = async (campaign) => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.post(`${API_URL}/campaigns/new_campaigns`, campaign, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { detail: 'Failed to create campaign' };
  }
};

export const get_dataanalysis = (month_year) => {
  return axios.get(`${API_URL}/agent-metrics/`, {
    params: {
      month_year
    }
  });
};

export const RegisterCustomerData = async (formData) => {
  try {
    const token = localStorage.getItem("token");
    console.log([...formData.entries()]);
    const response = await axios.post(`${API_URL}/campaigns/`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  } catch (error) {
    throw error.response?.data || { detail: "Form submission failed" };
  }
};

export const make_Calls = async (payload) => {
  return axios.post(`${API_URL}/make_call`, payload)
    .then(res => res.data);
};

export const getCampaign = async() => {
    try {
      const token = localStorage.getItem("token");

      const response = await axios.get(`${API_URL}/campaigns/get`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      return response.data; // [{ id: 1, name: "Campaign 1" }, ...]
    } catch (error) {
      console.error("Error fetching campaigns:", error);
      return [];
    }
};

export const get_Campaign = async() => {
    try {
      const token = localStorage.getItem("token");

      const response = await axios.get(`${API_URL}/campaigns/get_campaign`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      return response.data; // [{ id: 1, name: "Campaign 1" }, ...]
    } catch (error) {
      console.error("Error fetching campaigns:", error);
      return [];
    }
};

export const getCustomersByCampaign = async (campaignId) => {
  try {
    const token = localStorage.getItem("token");

    const response = await axios.get(`${API_URL}/campaigns/${campaignId}/customers`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data; // [{id, name, phone, status, conversation}, ...]
  } catch (error) {
    console.error("Error fetching customers:", error);
    return [];
  }
};

// ✅ Get all agents
export const getAgents = async () => {
  try {
    const response = await axios.get(`${ELEVEN_API}/agents`, {
      headers: {
        "xi-api-key": API_KEY,
      },
    });
    return response.data; // array of agents
  } catch (error) {
    console.error("Error fetching agents:", error);
    throw error;
  }
};