import axios from 'axios';

const rawBaseUrl = getCookie('BASEURL');
const BASEURL = rawBaseUrl ? rawBaseUrl.replace(/^"|"$/g, '') : null; // Remove any enclosing quotes
const API_URL = "https://redsocks.mu:9000";
// const API_URL = `${BASEURL}get_cd_info/`;
// const API_URL2 = `${BASEURL}print_receipt/`;

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

export class Service {
    startcall() {
        return axios.post(`${API_URL}/make_call/`);
    }
    get_data() {
        return axios.get(`${API_URL}/api/leadrat/variables/`);
    }
    get_dataanalysis() {
        return axios.get(`${API_URL}/agent-metrics/`);
    }
    fetch_data(id) {
        return axios.get(`${API_URL}/api/get_data/${id}`);
    }
    delete_lead(id) {
        return axios.get(`${API_URL}/leads/${id}/`);
    }
    add_data(data) {
        return axios.post(`${API_URL}/api/add_data/`, data, {
            headers: {
                "Content-Type": "application/json"
            }
        });
    }
}