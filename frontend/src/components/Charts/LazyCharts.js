import React, { lazy, Suspense } from 'react';

// Lazy load chart components to reduce initial bundle size
const BarChart = lazy(() => 
  import('react-chartjs-2').then(module => ({ default: module.Bar }))
);

const PieChart = lazy(() => 
  import('react-chartjs-2').then(module => ({ default: module.Pie }))
);

const LineChart = lazy(() => 
  import('react-chartjs-2').then(module => ({ default: module.Line }))
);

// Chart.js registration - only loaded when charts are needed
const registerChartJS = async () => {
  const { Chart: ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement, PointElement, LineElement } = await import('chart.js');
  
  ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    PointElement,
    LineElement
  );
};

// Chart wrapper with loading state
const ChartWrapper = ({ children }) => (
  <Suspense fallback={
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <span className="ml-2 text-gray-600">Loading chart...</span>
    </div>
  }>
    {children}
  </Suspense>
);

export const LazyBarChart = ({ data, options, ...props }) => {
  React.useEffect(() => {
    registerChartJS();
  }, []);

  return (
    <ChartWrapper>
      <BarChart data={data} options={options} {...props} />
    </ChartWrapper>
  );
};

export const LazyPieChart = ({ data, options, ...props }) => {
  React.useEffect(() => {
    registerChartJS();
  }, []);

  return (
    <ChartWrapper>
      <PieChart data={data} options={options} {...props} />
    </ChartWrapper>
  );
};

export const LazyLineChart = ({ data, options, ...props }) => {
  React.useEffect(() => {
    registerChartJS();
  }, []);

  return (
    <ChartWrapper>
      <LineChart data={data} options={options} {...props} />
    </ChartWrapper>
  );
};

export { BarChart, PieChart, LineChart };
export default { LazyBarChart, LazyPieChart, LazyLineChart };