
import * as Slider from '@radix-ui/react-slider'

interface Props {
  min: number
  max: number
  value: [number, number]
  onValueChange: (value: [number, number]) => void
  disabled?: boolean
}

export function RangeSlider({ min, max, value, onValueChange, disabled }: Props) {
  return (
    <Slider.Root
      className="relative flex w-full touch-none select-none items-center h-5"
      min={min}
      max={max}
      value={value}
      onValueChange={(val) => onValueChange(val as [number, number])}
      step={1}
      minStepsBetweenThumbs={1}
      disabled={disabled}
    >
      <Slider.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-surface-700">
        <Slider.Range className="absolute h-full bg-brand-500" />
      </Slider.Track>
      <Slider.Thumb
        className="block h-4 w-4 rounded-full bg-white border border-brand-500 shadow transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50 disabled:pointer-events-none disabled:opacity-50"
        aria-label="Min Confidence"
      />
      <Slider.Thumb
        className="block h-4 w-4 rounded-full bg-white border border-brand-500 shadow transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50 disabled:pointer-events-none disabled:opacity-50"
        aria-label="Max Confidence"
      />
    </Slider.Root>
  )
}
