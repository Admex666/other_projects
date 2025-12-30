import { useNavigate } from "react-router-dom";
import React from 'react';

export const Settings = () => {
    return (
        <div className="p-8">
            <h1 className="text-3xl font-bold mb-6">Settings</h1>
            <p className="text-gray-400">Configure game range, station lists, and debug mode.</p>
        </div>
    );
};
