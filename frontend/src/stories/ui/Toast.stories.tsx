import { ToastProvider, useToast } from '../../components/ui/Toast';

export default {
  title: 'UI/Toast',
  component: ToastProvider,
  parameters: {
    layout: 'centered',
  },
} as const;

function ToastDemo() {
  const { showToast } = useToast();
  
  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={() =>
          showToast({
            type: 'success',
            title: 'Success!',
            description: 'Operation completed successfully.',
          })
        }
        className="rounded-lg bg-green-500 px-4 py-2 text-white"
      >
        Show Success Toast
      </button>
      <button
        onClick={() =>
          showToast({
            type: 'error',
            title: 'Error!',
            description: 'Something went wrong.',
          })
        }
        className="rounded-lg bg-red-500 px-4 py-2 text-white"
      >
        Show Error Toast
      </button>
      <button
        onClick={() =>
          showToast({
            type: 'warning',
            title: 'Warning!',
            description: 'Please check your input.',
          })
        }
        className="rounded-lg bg-yellow-500 px-4 py-2 text-white"
      >
        Show Warning Toast
      </button>
      <button
        onClick={() =>
          showToast({
            type: 'info',
            title: 'Info!',
            description: 'Here\'s some information.',
          })
        }
        className="rounded-lg bg-blue-500 px-4 py-2 text-white"
      >
        Show Info Toast
      </button>
    </div>
  );
}

export const Default = () => (
  <ToastProvider>
    <ToastDemo />
  </ToastProvider>
);
Default.storyName = 'Toast Provider Demo';