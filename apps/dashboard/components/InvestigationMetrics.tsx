import {
  formatAgentName,
  formatCurrencyCost,
  formatDuration,
  formatNumber,
  formatPercent,
  formatPricingPeriod,
  formatRatePerMillion,
} from "@/lib/format";
import type React from "react";
import type {
  InvestigationMetrics as Metrics,
  PricingRateSet,
} from "@/types/investigation";

type MetricItem = {
  label: string;
  value: string;
  title?: string;
  badge?: boolean;
};

export function InvestigationMetrics({ metrics }: { metrics: Metrics | null }) {
  if (!metrics) {
    return null;
  }

  const currency = metrics.pricing_currency ?? "USD";
  const hasPricingMetadata = Boolean(
    metrics.pricing_model ||
      metrics.pricing_period ||
      metrics.pricing_rates_per_1m,
  );
  const estimatedCost =
    metrics.estimated_cost_usd === 0 && !hasPricingMetadata
      ? "Unavailable"
      : formatCurrencyCost(metrics.estimated_cost_usd, currency);
  const cacheHitPercent = getCacheHitPercent(metrics);
  const cacheMissPercent =
    typeof cacheHitPercent === "number" ? Math.max(0, 100 - cacheHitPercent) : null;

  const executionMetrics = compactItems([
    numberItem("Duration", metrics.duration_seconds, formatDuration),
    agentItem(metrics.agents_used),
    numberItem("Tool calls", metrics.tool_calls),
    numberItem("LLM calls", metrics.llm_calls),
  ]);

  const tokenMetrics = compactItems([
    numberItem("Input tokens", metrics.input_tokens),
    numberItem("Cache hit", metrics.input_cache_hit_tokens, formatNumber, {
      title: "Input tokens served from DeepSeek prompt cache.",
    }),
    numberItem("Cache miss", metrics.input_cache_miss_tokens, formatNumber, {
      title: "Input tokens billed at the normal uncached input rate.",
    }),
    numberItem("Cache hit ratio", cacheHitPercent, formatPercent),
    numberItem("Output tokens", metrics.output_tokens),
    numberItem("Reasoning tokens", metrics.reasoning_tokens),
    numberItem("Total tokens", metrics.total_tokens),
  ]);

  const pricingMetrics = compactItems([
    textItem("Model", metrics.pricing_model),
    metrics.pricing_period
      ? textItem("Period", formatPricingPeriod(metrics.pricing_period), { badge: true })
      : null,
    numberItem("Peak calls", metrics.peak_llm_calls),
    numberItem("Off-peak calls", metrics.off_peak_llm_calls),
    typeof metrics.estimated_cost_usd === "number" || hasPricingMetadata
      ? { label: "Estimated cost", value: estimatedCost }
      : null,
  ]);

  return (
    <section className="panel metrics-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Usage</p>
          <h2>Investigation metrics</h2>
        </div>
      </div>
      <div className="metrics-groups">
        {executionMetrics.length > 0 && (
          <MetricGroup title="Execution" items={executionMetrics} />
        )}
        {tokenMetrics.length > 0 && (
          <MetricGroup title="Token usage" items={tokenMetrics}>
            <CacheUsage
              hitTokens={metrics.input_cache_hit_tokens}
              missTokens={metrics.input_cache_miss_tokens}
              hitPercent={cacheHitPercent}
              missPercent={cacheMissPercent}
            />
          </MetricGroup>
        )}
        {pricingMetrics.length > 0 && (
          <MetricGroup title="Pricing" items={pricingMetrics}>
            <PricingDetails metrics={metrics} currency={currency} />
          </MetricGroup>
        )}
      </div>
    </section>
  );
}

function MetricGroup({
  title,
  items,
  children,
}: {
  title: string;
  items: MetricItem[];
  children?: React.ReactNode;
}) {
  return (
    <div className="metrics-group">
      <h3>{title}</h3>
      <div className="metrics-grid">
        {items.map((item) => (
          <MetricCard key={item.label} item={item} />
        ))}
      </div>
      {children}
    </div>
  );
}

function MetricCard({ item }: { item: MetricItem }) {
  return (
    <div className="metric-card" title={item.title}>
      <span>{item.label}</span>
      <strong className={item.badge ? "pricing-period-badge" : undefined}>
        {item.value}
      </strong>
    </div>
  );
}

function CacheUsage({
  hitTokens,
  missTokens,
  hitPercent,
  missPercent,
}: {
  hitTokens?: number | null;
  missTokens?: number | null;
  hitPercent: number | null;
  missPercent: number | null;
}) {
  if (
    typeof hitTokens !== "number" &&
    typeof missTokens !== "number" &&
    typeof hitPercent !== "number"
  ) {
    return null;
  }

  const width = typeof hitPercent === "number" ? clamp(hitPercent, 0, 100) : 0;
  const label =
    typeof hitPercent === "number"
      ? `${formatPercent(hitPercent)} cached`
      : "Cache usage unavailable";

  return (
    <div className="cache-usage">
      <div className="cache-usage-header">
        <span>Input cache usage</span>
        <strong>{label}</strong>
      </div>
      <div
        className="cache-bar"
        role="img"
        aria-label={`Input cache usage: ${label}. Cache hit tokens ${formatNumber(
          hitTokens,
        )}. Cache miss tokens ${formatNumber(missTokens)}.`}
      >
        <span style={{ width: `${width}%` }} />
      </div>
      <div className="cache-breakdown">
        <div title="Input tokens served from DeepSeek prompt cache.">
          <span>Cache hit</span>
          <strong>{formatNumber(hitTokens)}</strong>
          {typeof hitPercent === "number" && <em>{formatPercent(hitPercent)}</em>}
        </div>
        <div title="Input tokens billed at the normal uncached input rate.">
          <span>Cache miss</span>
          <strong>{formatNumber(missTokens)}</strong>
          {typeof missPercent === "number" && <em>{formatPercent(missPercent)}</em>}
        </div>
      </div>
    </div>
  );
}

function PricingDetails({
  metrics,
  currency,
}: {
  metrics: Metrics;
  currency: string;
}) {
  const hasRates = Boolean(metrics.pricing_rates_per_1m);
  const hasSplits = Boolean(
    metrics.peak_cache_hit_tokens ||
      metrics.peak_cache_miss_tokens ||
      metrics.peak_output_tokens ||
      metrics.off_peak_cache_hit_tokens ||
      metrics.off_peak_cache_miss_tokens ||
      metrics.off_peak_output_tokens,
  );

  if (!hasRates && !hasSplits) {
    return null;
  }

  return (
    <details className="pricing-details">
      <summary>Pricing rates used - {currency} per 1M tokens</summary>
      {hasRates && (
        <div className="pricing-detail-grid">
          <RateSet
            title="Off-Peak"
            rates={metrics.pricing_rates_per_1m?.off_peak}
            currency={currency}
          />
          <RateSet
            title="Peak"
            rates={metrics.pricing_rates_per_1m?.peak}
            currency={currency}
          />
        </div>
      )}
      {hasSplits && (
        <div className="pricing-split-grid">
          <TokenSplit
            title="Off-Peak token split"
            cacheHit={metrics.off_peak_cache_hit_tokens}
            cacheMiss={metrics.off_peak_cache_miss_tokens}
            output={metrics.off_peak_output_tokens}
          />
          <TokenSplit
            title="Peak token split"
            cacheHit={metrics.peak_cache_hit_tokens}
            cacheMiss={metrics.peak_cache_miss_tokens}
            output={metrics.peak_output_tokens}
          />
        </div>
      )}
    </details>
  );
}

function RateSet({
  title,
  rates,
  currency,
}: {
  title: string;
  rates?: PricingRateSet | null;
  currency: string;
}) {
  if (!rates) {
    return null;
  }

  return (
    <div className="pricing-detail-card">
      <h4>{title}</h4>
      <DetailRow label="Cache hit" value={formatRatePerMillion(rates.cache_hit, currency)} />
      <DetailRow
        label="Cache miss"
        value={formatRatePerMillion(rates.cache_miss, currency)}
      />
      <DetailRow label="Output" value={formatRatePerMillion(rates.output, currency)} />
    </div>
  );
}

function TokenSplit({
  title,
  cacheHit,
  cacheMiss,
  output,
}: {
  title: string;
  cacheHit?: number | null;
  cacheMiss?: number | null;
  output?: number | null;
}) {
  if (
    typeof cacheHit !== "number" &&
    typeof cacheMiss !== "number" &&
    typeof output !== "number"
  ) {
    return null;
  }

  return (
    <div className="pricing-detail-card">
      <h4>{title}</h4>
      <DetailRow label="Cache hit" value={formatNumber(cacheHit)} />
      <DetailRow label="Cache miss" value={formatNumber(cacheMiss)} />
      <DetailRow label="Output" value={formatNumber(output)} />
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="pricing-detail-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function getCacheHitPercent(metrics: Metrics) {
  if (
    typeof metrics.cache_hit_ratio_percent === "number" &&
    !Number.isNaN(metrics.cache_hit_ratio_percent)
  ) {
    return metrics.cache_hit_ratio_percent;
  }

  if (
    typeof metrics.input_cache_hit_tokens !== "number" ||
    typeof metrics.input_tokens !== "number" ||
    metrics.input_tokens <= 0
  ) {
    return null;
  }

  return (metrics.input_cache_hit_tokens / metrics.input_tokens) * 100;
}

function compactItems(items: Array<MetricItem | null>) {
  return items.filter((item): item is MetricItem => item !== null);
}

function numberItem(
  label: string,
  value?: number | null,
  formatter: (value: number) => string = formatNumber,
  options: Pick<MetricItem, "title"> = {},
) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return null;
  }

  return { label, value: formatter(value), ...options };
}

function textItem(
  label: string,
  value?: string | null,
  options: Pick<MetricItem, "badge"> = {},
) {
  if (!value) {
    return null;
  }

  return { label, value, ...options };
}

function agentItem(agents?: string[] | null) {
  if (!Array.isArray(agents)) {
    return null;
  }

  return {
    label: "Agents used",
    value: agents.length ? agents.map(formatAgentName).join(", ") : "None",
  };
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
