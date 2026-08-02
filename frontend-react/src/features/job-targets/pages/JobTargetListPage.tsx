/**
 * Job Target List Page
 *
 * Displays all job targets with filtering and creation options.
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { jobTargetApi, type JobTargetResponse } from '../api/job-targets';

const JobTargetListPage: React.FC = () => {
  const navigate = useNavigate();
  const [levelFilter, setLevelFilter] = React.useState<string>('');

  const { data: jobTargets, isLoading, error } = useQuery({
    queryKey: ['job-targets', { level: levelFilter || undefined }],
    queryFn: () => jobTargetApi.list(levelFilter ? { level: levelFilter } : undefined),
  });

  if (isLoading) {
    return <div style={styles.loading}>加载中...</div>;
  }

  if (error) {
    return <div style={styles.error}>加载失败: {(error as Error).message}</div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>岗位目标管理</h1>
        <button
          style={styles.createButton}
          onClick={() => navigate('/job-targets/new')}
        >
          + 创建新Job Target
        </button>
      </div>

      <div style={styles.filterBar}>
        <label style={styles.filterLabel}>
          级别筛选:
          <select
            style={styles.filterSelect}
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
          >
            <option value="">全部</option>
            <option value="intern">实习生</option>
            <option value="junior">初级</option>
            <option value="mid">中级</option>
            <option value="senior">高级</option>
            <option value="staff">专家</option>
          </select>
        </label>
      </div>

      {jobTargets && jobTargets.length === 0 ? (
        <div style={styles.empty}>
          <p>暂无岗位目标</p>
          <button
            style={styles.createButton}
            onClick={() => navigate('/job-targets/new')}
          >
            创建第一个Job Target
          </button>
        </div>
      ) : (
        <div style={styles.grid}>
          {jobTargets?.map((jobTarget) => (
            <JobTargetCard
              key={jobTarget.job_target_id}
              jobTarget={jobTarget}
              onClick={() => navigate(`/job-targets/${jobTarget.job_target_id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================================
// Job Target Card Component
// ============================================================

interface JobTargetCardProps {
  jobTarget: JobTargetResponse;
  onClick: () => void;
}

const JobTargetCard: React.FC<JobTargetCardProps> = ({ jobTarget, onClick }) => {
  const levelLabels: Record<string, string> = {
    intern: '实习生',
    junior: '初级',
    mid: '中级',
    senior: '高级',
    staff: '专家',
  };

  const sourceLabels: Record<string, string> = {
    template: '模板',
    pasted_jd: 'JD解析',
    manual: '手动创建',
  };

  return (
    <div style={styles.card} onClick={onClick}>
      <div style={styles.cardHeader}>
        <h3 style={styles.cardTitle}>{jobTarget.title}</h3>
        <span style={styles.levelBadge}>
          {levelLabels[jobTarget.level] || jobTarget.level}
        </span>
      </div>

      <div style={styles.cardBody}>
        {jobTarget.description && (
          <p style={styles.cardDescription}>{jobTarget.description}</p>
        )}

        <div style={styles.cardMeta}>
          <div style={styles.metaItem}>
            <span style={styles.metaLabel}>能力要求:</span>
            <span style={styles.metaValue}>{jobTarget.requirements.length} 项</span>
          </div>
          <div style={styles.metaItem}>
            <span style={styles.metaLabel}>来源:</span>
            <span style={styles.metaValue}>
              {sourceLabels[jobTarget.source] || jobTarget.source}
            </span>
          </div>
          <div style={styles.metaItem}>
            <span style={styles.metaLabel}>创建时间:</span>
            <span style={styles.metaValue}>
              {new Date(jobTarget.created_at).toLocaleDateString('zh-CN')}
            </span>
          </div>
        </div>
      </div>

      <div style={styles.cardFooter}>
        <button
          style={styles.viewButton}
          onClick={(e) => {
            e.stopPropagation();
            onClick();
          }}
        >
          查看详情 →
        </button>
      </div>
    </div>
  );
};

// ============================================================
// Styles
// ============================================================

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '24px',
    maxWidth: '1200px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },
  title: {
    fontSize: '28px',
    fontWeight: '600',
    margin: '0',
  },
  createButton: {
    padding: '10px 20px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
  },
  filterBar: {
    marginBottom: '24px',
    padding: '16px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
  },
  filterLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    fontSize: '14px',
    fontWeight: '500',
  },
  filterSelect: {
    padding: '8px 12px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '14px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
    gap: '20px',
  },
  card: {
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    padding: '20px',
    backgroundColor: 'white',
    cursor: 'pointer',
    transition: 'box-shadow 0.2s, transform 0.2s',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '12px',
  },
  cardTitle: {
    fontSize: '18px',
    fontWeight: '600',
    margin: '0',
    flex: '1',
  },
  levelBadge: {
    padding: '4px 12px',
    backgroundColor: '#dbeafe',
    color: '#1e40af',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '500',
  },
  cardBody: {
    marginBottom: '16px',
  },
  cardDescription: {
    fontSize: '14px',
    color: '#6b7280',
    marginBottom: '16px',
    lineHeight: '1.5',
  },
  cardMeta: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  metaItem: {
    display: 'flex',
    gap: '8px',
    fontSize: '13px',
  },
  metaLabel: {
    color: '#6b7280',
    fontWeight: '500',
  },
  metaValue: {
    color: '#111827',
  },
  cardFooter: {
    borderTop: '1px solid #f3f4f6',
    paddingTop: '12px',
  },
  viewButton: {
    padding: '8px 16px',
    backgroundColor: 'transparent',
    color: '#3b82f6',
    border: '1px solid #3b82f6',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
    width: '100%',
  },
  empty: {
    textAlign: 'center',
    padding: '60px 20px',
    color: '#6b7280',
  },
  loading: {
    textAlign: 'center',
    padding: '60px 20px',
    fontSize: '16px',
    color: '#6b7280',
  },
  error: {
    textAlign: 'center',
    padding: '60px 20px',
    fontSize: '16px',
    color: '#dc2626',
  },
};

export default JobTargetListPage;
