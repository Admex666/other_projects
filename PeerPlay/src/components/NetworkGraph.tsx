'use client'

import React, { useEffect, useState } from 'react'
import CytoscapeComponent from 'react-cytoscapejs'
import { User, Interaction, SurveyResponse } from '@prisma/client'

type Participant = { user: User }

export default function NetworkGraph({
    participants,
    interactions,
    surveyResponses
}: {
    participants: Participant[]
    interactions: Interaction[]
    surveyResponses: SurveyResponse[]
}) {
    const [elements, setElements] = useState<any[]>([])

    useEffect(() => {
        const nodes = participants.map((p) => ({
            data: { id: p.user.id, label: p.user.name, role: p.user.role },
            classes: 'participant'
        }))

        // Objective Network: Trades
        const tradeEdges = interactions.map((i) => ({
            data: {
                source: i.fromUserId,
                target: i.toUserId,
                label: `${i.quantity} ${i.resourceType}`,
                type: 'trade'
            },
            classes: 'trade-edge'
        }))

        // Perceived Network: Surveys (only show if rating > 3 to filter noise)
        const surveyEdges = surveyResponses
            .filter((s) => s.answer >= 3 && s.targetUserId)
            .map((s) => ({
                data: {
                    source: s.userId,
                    target: s.targetUserId as string,
                    label: `Rating: ${s.answer}`,
                    type: 'survey'
                },
                classes: 'survey-edge'
            }))

        setElements([...nodes, ...tradeEdges, ...surveyEdges])
    }, [participants, interactions, surveyResponses])

    return (
        <div className="border border-gray-200 rounded-lg overflow-hidden bg-white mt-4" style={{ height: '500px' }}>
            <CytoscapeComponent
                elements={elements}
                style={{ width: '100%', height: '100%' }}
                layout={{ name: 'circle' }}
                stylesheet={[
                    {
                        selector: 'node',
                        style: {
                            'background-color': '#4F46E5', // Indigo-600
                            label: 'data(label)',
                            color: '#111827',
                            'font-size': '12px',
                            'text-valign': 'bottom',
                            'text-margin-y': 5
                        }
                    },
                    {
                        selector: '.trade-edge',
                        style: {
                            width: 2,
                            'line-color': '#10B981', // Emerald-500
                            'target-arrow-color': '#10B981',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            label: 'data(label)',
                            'font-size': '10px',
                            'text-rotation': 'autorotate' as any,
                            'text-background-color': '#ffffff',
                            'text-background-opacity': 0.8 as any
                        }
                    },
                    {
                        selector: '.survey-edge',
                        style: {
                            width: 1,
                            'line-color': '#F59E0B', // Amber-500
                            'target-arrow-color': '#F59E0B',
                            'target-arrow-shape': 'triangle',
                            'line-style': 'dashed',
                            'curve-style': 'unbundled-bezier',
                            label: 'data(label)',
                            'font-size': '10px',
                            'text-rotation': 'autorotate' as any,
                            'text-background-color': '#ffffff',
                            'text-background-opacity': 0.8 as any
                        }
                    }
                ]}
            />
        </div>
    )
}
