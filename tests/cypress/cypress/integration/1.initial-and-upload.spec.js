// <reference types="cypress" />

const csvfiles = require('../fixtures/csvfiles')

describe('Initial app state', () => {

  // Uncomment if running Cypress directly rather than via 'npm run ci'
  before(() => {
    cy.visit('http://127.0.0.1:8000/clear')
  })

  beforeEach(() => {
    cy.visit('http://127.0.0.1:8000')
  })

  it('Shows sidebar with page title on initial load', () => {
    cy.get('#sidebar')
      .contains('h1', 'Benford\'s Law Test')
  })

  it('Shows "None" for file count if no files are uploaded', () => {
    cy.get('#uploaded-files-count')
      .should('have.text', 'None')
  })

  it('Shows file upload form control', () => {
    cy.get('#upload-file')
      .find('input[id=upload-file-input]')
      .should('exist')
  })

  it('Has empty file selection dropdown', () => {
    cy.get('#uploaded-files-select')
      .should('be.empty')
      .find(':selected')
      .should('not.exist')
  })
})

describe('Uploading .csv files', () => {
  before(() => {
    cy.visit('http://127.0.0.1:8000')
  })
  let uploadedFileCount = 0
  csvfiles.valid.forEach((csvfile) => {
    describe(`Upload: ${csvfile.filename}`, () => {
      before(() => {
        cy.get('#upload-file')
          // cypress annoyingly fails to find specs when fixtureFolder is set to relative path
          .attachFile({ filePath: `../fixtures/${csvfile.filename}`, fileName: csvfile.filename })
          .wait(100)
          .then(() => {
            uploadedFileCount++
          })
        // .wait(5000)
        // })
      })
      it('Shows preview upon upload but not analysis', () => {
        cy.get('#preview').should('exist')
        cy.get('#analysis').should('not.exist')
      })
      it('Shows newly uploaded .csv file in preview', () => {
        cy.get('#csv-filename')
          .should('have.text', `File: ${csvfile.filename}`)
      })
      it('Does not display status message', () => {
        cy.get('#status-message')
          .should('not.exist')
      })
      it('Updates file select element after upload', () => {
        cy.get('#uploaded-files-select')
          .find('option')
          .should('have.length', uploadedFileCount)
      })
      it('Selects newly uploaded .csv file in dropdown', () => {
        cy.get('#uploaded-files-select')
          .find(':selected')
          .should('have.text', csvfile.filename)
      })
      it('Updates uploaded file count after upload', () => {
        cy.get('#uploaded-files-count')
          .should('have.text', uploadedFileCount)
      })
    })
  })
})
