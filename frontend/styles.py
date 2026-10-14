import streamlit as st


def apply_global_styles() -> None:
    """
    Injects custom CSS for a cohesive, modern AI SaaS dashboard aesthetic.
    Features professional indigo/violet accents, clean card styling,
    readable typography, and clear status badges.
    """
    st.markdown(
        """
        <style>
        /* Global typography & spacing */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }

        /* Gradient header text */
        .brand-header-title {
            font-size: 2.1rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem;
            display: inline-block;
        }

        .brand-header-subtitle {
            color: #94a3b8;
            font-size: 0.95rem;
            font-weight: 500;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 1.5rem;
        }

        .page-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.2rem;
        }

        .page-description {
            color: #94a3b8;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }

        /* Glassmorphism Cards */
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -2px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(8px);
        }

        .glass-card-accent {
            border-left: 4px solid #6366f1;
        }

        /* Status Badges */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.025em;
        }

        .status-badge-healthy {
            background-color: rgba(6, 95, 70, 0.35);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.3);
        }

        .status-badge-degraded {
            background-color: rgba(146, 64, 14, 0.35);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.3);
        }

        .status-badge-disconnected {
            background-color: rgba(127, 29, 29, 0.35);
            color: #f87171;
            border: 1px solid rgba(248, 113, 113, 0.3);
        }

        .status-badge-published {
            background-color: rgba(99, 102, 241, 0.25);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.4);
        }

        /* Post preview container */
        .post-preview-container {
            background: #111827;
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .post-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1f2937;
            padding-bottom: 0.75rem;
            margin-bottom: 1rem;
        }

        .post-preview-body {
            font-size: 1rem;
            line-height: 1.65;
            color: #e5e7eb;
            white-space: pre-wrap;
            font-family: inherit;
            background: #1e293b;
            padding: 1.25rem;
            border-radius: 8px;
            border: 1px solid #334155;
            margin-bottom: 1rem;
        }

        .meta-pill {
            display: inline-block;
            background: #1e293b;
            color: #94a3b8;
            border: 1px solid #334155;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-family: monospace;
            margin-right: 6px;
            margin-bottom: 6px;
        }

        /* Callout notification */
        .alert-callout {
            border-radius: 8px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            display: flex;
            gap: 10px;
            align-items: flex-start;
        }

        .alert-callout-warning {
            background-color: rgba(146, 64, 14, 0.2);
            border: 1px solid rgba(245, 158, 11, 0.4);
            color: #fde68a;
        }

        .alert-callout-info {
            background-color: rgba(30, 58, 138, 0.2);
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: #bfdbfe;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
