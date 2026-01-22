import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const useData = (datasetType) => {
    const [data, setData] = useState([]);
    const [detailedData, setDetailedData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [detailedLoading, setDetailedLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`http://localhost:8000/data/${datasetType}`);
            setData(response.data.data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [datasetType]);

    const fetchDetailed = useCallback(async (sensor = null) => {
        setDetailedLoading(true);
        try {
            const url = `http://localhost:8000/data-detailed/${datasetType}${sensor ? `?sensor=${sensor}` : ''}`;
            const response = await axios.get(url);
            setDetailedData(response.data.data);
        } catch (err) {
            console.error("Error fetching detailed data:", err);
        } finally {
            setDetailedLoading(false);
        }
    }, [datasetType]);

    const fetchScanPoints = useCallback(async (sensor, setup, filename) => {
        try {
            const response = await axios.get(`http://localhost:8000/scan-points/${datasetType}/${sensor}/${setup}/${filename}`);
            return response.data.points;
        } catch (err) {
            console.error("Error fetching scan points:", err);
            return [];
        }
    }, [datasetType]);

    const fetchGTRow = useCallback(async (sensor, setup, sampleId) => {
        try {
            const response = await axios.get(`http://localhost:8000/ground-truth-detail/${datasetType}/${sensor}/${setup}/${sampleId}`);
            return response.data.data;
        } catch (err) {
            console.error("Error fetching GT detail:", err);
            return null;
        }
    }, [datasetType]);

    useEffect(() => {
        if (datasetType) {
            fetchData();
            fetchDetailed();
        }
    }, [datasetType, fetchData, fetchDetailed]);

    return {
        data,
        detailedData,
        loading,
        detailedLoading,
        error,
        fetchDetailed,
        fetchScanPoints,
        fetchGTRow
    };
};

export default useData;
