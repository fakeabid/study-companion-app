import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StorageUsageWidget } from '../components/StorageUsageWidget'

describe('StorageUsageWidget', () => {
  it('renders storage usage details', () => {
    render(
      <StorageUsageWidget
        storage={{
          used_bytes: 536870912,
          used_display: '512.0 MB',
          remaining_bytes: 536870912,
          remaining_display: '512.0 MB',
          quota_bytes: 1073741824,
          quota_display: '1.0 GB',
          percent_used: 50,
        }}
      />,
    )

    expect(screen.getByText('Storage usage')).toBeInTheDocument()
    expect(screen.getByText('512.0 MB of 1.0 GB used')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
    expect(screen.getByText('512.0 MB remaining')).toBeInTheDocument()
  })

  it('shows loading state when storage is unavailable', () => {
    render(<StorageUsageWidget storage={null} />)
    expect(screen.getByText('Loading storage usage...')).toBeInTheDocument()
  })
})

describe('FileUploadZone', () => {
  it('calls onUpload when a file is selected', async () => {
    const onUpload = vi.fn().mockResolvedValue(undefined)
    const { FileUploadZone } = await import('../components/FileUploadZone')
    const user = userEvent.setup()

    render(
      <FileUploadZone
        onUpload={onUpload}
        uploading={false}
        uploadProgress={0}
        error={null}
        successMessage={null}
      />,
    )

    const input = document.querySelector('input[type="file"]')
    const file = new File(['notes'], 'notes.pdf', { type: 'application/pdf' })
    await user.upload(input, file)

    expect(onUpload).toHaveBeenCalledWith(file)
  })
})
