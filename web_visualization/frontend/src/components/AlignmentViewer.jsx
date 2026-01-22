import React, { useRef, useMemo, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Points, PointMaterial, Center } from '@react-three/drei';
import * as THREE from 'three';
import { motion, AnimatePresence } from 'framer-motion';

function PointCloud({ points, color, size = 0.05, opacity = 1.0, matrix }) {
    const pointsArr = useMemo(() => {
        if (!points || points.length === 0) return new Float32Array(0);
        const positions = new Float32Array(points.length * 3);
        for (let i = 0; i < points.length; i++) {
            positions[i * 3] = points[i][0];
            positions[i * 3 + 1] = points[i][1];
            positions[i * 3 + 2] = points[i][2];
        }
        return positions;
    }, [points]);

    const groupRef = useRef();

    useEffect(() => {
        if (groupRef.current && matrix) {
            groupRef.current.matrixAutoUpdate = false;
            groupRef.current.matrix.copy(matrix);
        } else if (groupRef.current) {
            groupRef.current.matrixAutoUpdate = true;
            groupRef.current.matrix.identity();
        }
    }, [matrix]);

    if (pointsArr.length === 0) return null;

    return (
        <group ref={groupRef}>
            <Points positions={pointsArr}>
                <PointMaterial
                    transparent
                    vertexColors={false}
                    size={size}
                    sizeAttenuation={true}
                    depthWrite={false}
                    color={color}
                    opacity={opacity}
                />
            </Points>
        </group>
    );
}

const AlignmentViewer = ({ scanPoints, referencePoints, matrix }) => {

    return (
        <div className="w-full h-[500px] bg-gray-950 rounded-xl overflow-hidden border border-gray-800 relative group">
            <Canvas dpr={[1, 2]} camera={{ position: [1.5, 1.5, 1.5], fov: 45 }}>
                <color attach="background" args={['#030712']} />
                <OrbitControls makeDefault enableDamping dampingFactor={0.05} />

                <ambientLight intensity={1.5} />
                <pointLight position={[10, 10, 10]} intensity={2} />

                <gridHelper args={[10, 10, 0x334155, 0x1e293b]} position={[0, -1, 0]} />

                <group rotation={[-Math.PI / 2, 0, 0]}>
                    {/* Fixed Reference Torso */}
                    <PointCloud
                        points={referencePoints}
                        color="#10b981"
                        size={0.005}
                        opacity={0.4}
                    />

                    {/* Moving Scan Data */}
                    <PointCloud
                        points={scanPoints}
                        color="#ec4899"
                        size={0.006}
                        opacity={1.0}
                        matrix={matrix}
                    />
                </group>
            </Canvas>

            <div className="absolute top-4 left-4 flex flex-col gap-2 pointer-events-none">
                <div className="flex items-center gap-2 bg-gray-900/90 backdrop-blur-md px-3 py-1.5 rounded-full border border-gray-700 shadow-2xl">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                    <span className="text-xs font-bold text-gray-200">Reference Model</span>
                </div>
                <div className="flex items-center gap-2 bg-gray-900/90 backdrop-blur-md px-3 py-1.5 rounded-full border border-gray-700 shadow-2xl">
                    <div className="w-2 h-2 rounded-full bg-pink-500 shadow-[0_0_8px_rgba(236,72,153,0.5)]" />
                    <span className="text-xs font-bold text-gray-200">Current Scan</span>
                </div>
            </div>

            <div className="absolute bottom-4 right-4 text-[10px] text-gray-400 bg-gray-900/80 backdrop-blur px-2.5 py-1.5 rounded-lg border border-gray-800 tracking-widest font-bold">
                DRAG • SCROLL • ZOOM
            </div>
        </div>
    );
};
;

export default AlignmentViewer;
