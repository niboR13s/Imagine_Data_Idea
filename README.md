# MRI PPS Data Idea

## Introduction

# Dashboard for data analysis and visualization

## Sensor Analysis Visualizer

This project is designed to visualize and analyze MRI sensor data generated from Blender simulations. It provides an interactive dashboard to explore performance metrics, error correlations, and time execution across different test scenarios.

### Project Overview

The `web_visualization` directory contains a full-stack application built to process and display data from Excel files (`Analysis_Extreme test.xlsx` and `Analysis_Hard test.xlsx`). 

#### Key Features
- **Interactive Dashboard**: Switch between "Extreme Test" and "Hard Test" datasets.
- **KPI Metrics**: Real-time calculation of Average Fitness, Rotation Error, Translation Error, and Execution Time.
- **Performance Charts**:
    - **Fitness Score by Position**: Bar chart showing optimization results.
    - **Errors (Rotation & Translation)**: Line chart with dual Y-axes for precise error tracking.
    - **RMSE by Position**: Line chart showing Root Mean Square Error.
    - **Total Time Execution**: Vertical bar chart highlighting time-intensive positions.
- **Error Correlations**: Scatter plots correlating object rotation magnitude with tracking errors.
- **Backend Caching**: High-performance data serving with optimized Excel parsing and memory caching.

---

#### Getting Started

##### Prerequisites
- Python 3.10+
- Node.js & npm

##### Backend Setup (FastAPI)
The backend serves the processed data via a REST API.

1. Navigate to the backend directory:
   ```bash
   cd web_visualization/backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the backend server:
   ```bash
   python main.py
   ```
   *The API will be available at `http://localhost:8000`*

##### Frontend Setup (React + Vite)
The frontend provides the interactive visualization dashboard.

1. Navigate to the frontend directory:
   ```bash
   cd web_visualization/frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   *The dashboard will be available at `http://localhost:5173`*

---

#### Project Structure

- `web_visualization/`
    - `backend/`: FastAPI application, data processing logic, and Excel parsers.
    - `frontend/`: React components, custom hooks for data fetching, and Recharts visualizations.
- `Blender_Generated_Data/`: Source Excel files and simulation data.
- `scripts/`: Python utility scripts for data inspection and validation.

---

#### Technologies Used
- **Backend**: FastAPI, Pandas, NumPy, Uvicorn
- **Frontend**: React, Vite, Recharts, TailwindCSS (Vanilla CSS for custom styling)
- **Data Source**: Microsoft Excel (.xlsx) parsed from Blender simulation outputs.
