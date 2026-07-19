import { render, screen } from '@testing-library/react'
import Page from './page'

describe('Home Page', () => {
  it('renders a heading', () => {
    // Basic test to ensure it renders without crashing
    render(<Page />)
    expect(document.body).toBeInTheDocument()
  })
})
