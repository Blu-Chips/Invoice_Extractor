import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Download, Settings, Eye, Send, CreditCard, Smartphone, AlertTriangle, Clock, Shield } from 'lucide-react';

const InvoiceExtractor = () => {
  const [currentStep, setCurrentStep] = useState('upload');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [extractedText, setExtractedText] = useState('');
  const [extractedData, setExtractedData] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [googleSheetsUrl, setGoogleSheetsUrl] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [userCredits, setUserCredits] = useState(0);
  const [showPayment, setShowPayment] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [paymentAmount, setPaymentAmount] = useState(50); // KES 50 per invoice
  const [errorLogs, setErrorLogs] = useState([]);
  const [userId] = useState(() => 'user_' + Math.random().toString(36).substr(2, 9));
  const fileInputRef = useRef(null);

  // Standard invoice fields that will be mapped to Google Sheets columns
  const standardFields = [
    'Invoice Number',
    'Invoice Date', 
    'Vendor Name',
    'Vendor Address',
    'Total Amount',
    'Tax Amount',
    'Subtotal',
    'Due Date',
    'Purchase Order',
    'Description'
  ];

  // Error logging function
  const logError = (error, context = '', severity = 'error') => {
    const errorLog = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      userId,
      error: error.message || error,
      context,
      severity,
      stack: error.stack || 'No stack trace available'
    };
    
    setErrorLogs(prev => [errorLog, ...prev.slice(0, 49)]); // Keep last 50 errors
    console.error('Error logged:', errorLog);
    
    // In production, send to error tracking service
    // sendToErrorTrackingService(errorLog);
  };

  // Initialize user credits on load
  useEffect(() => {
    const savedCredits = localStorage.getItem(`credits_${userId}`) || '5'; // 5 free credits
    setUserCredits(parseInt(savedCredits));
  }, [userId]);

  // Save credits to storage
  const saveCredits = (credits) => {
    setUserCredits(credits);
    localStorage.setItem(`credits_${userId}`, credits.toString());
  };

  // M-Pesa STK Push Integration
  const initiateMpesaPayment = async () => {
    if (!phoneNumber || !/^254\d{9}$/.test(phoneNumber)) {
      setError('Please enter a valid M-Pesa number (254XXXXXXXXX)');
      return;
    }

    setIsProcessing(true);
    setPaymentStatus('Initiating M-Pesa payment...');

    try {
      // Simulate M-Pesa Daraja API call
      const mpesaResponse = await simulateMpesaSTKPush();
      
      if (mpesaResponse.success) {
        setPaymentStatus('Payment request sent to your phone. Please complete the payment.');
        // Poll for payment status
        pollPaymentStatus(mpesaResponse.checkoutRequestId);
      } else {
        throw new Error(mpesaResponse.message || 'Payment initiation failed');
      }
    } catch (err) {
      logError(err, 'M-Pesa payment initiation', 'error');
      setError(`Payment failed: ${err.message}`);
      setIsProcessing(false);
    }
  };

  const simulateMpesaSTKPush = async () => {
    // Simulate Daraja API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // In production, this would be:
    /*
    const response = await fetch('/api/mpesa/stkpush', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phoneNumber,
        amount: paymentAmount,
        accountReference: `INV_CREDITS_${userId}`,
        transactionDesc: 'Invoice Processing Credits'
      })
    });
    */
    
    return {
      success: true,
      checkoutRequestId: 'ws_CO_' + Date.now(),
      message: 'STK Push sent successfully'
    };
  };

  const pollPaymentStatus = async (checkoutRequestId) => {
    let attempts = 0;
    const maxAttempts = 30; // 5 minutes max
    
    const poll = async () => {
      try {
        attempts++;
        setPaymentStatus(`Waiting for payment confirmation... (${attempts}/${maxAttempts})`);
        
        // Simulate payment status check
        const status = await simulatePaymentStatusCheck(checkoutRequestId);
        
        if (status.resultCode === '0') {
          // Payment successful
          const creditsToAdd = Math.floor(paymentAmount / 10); // 1 credit per KES 10
          saveCredits(userCredits + creditsToAdd);
          setPaymentStatus(`Payment successful! ${creditsToAdd} credits added.`);
          setShowPayment(false);
          setIsProcessing(false);
          
          // Log successful payment
          logError({message: `Payment successful: ${paymentAmount} KES, ${creditsToAdd} credits added`}, 'payment_success', 'info');
          
        } else if (status.resultCode === '1032') {
          // Payment cancelled
          setError('Payment was cancelled by user');
          setIsProcessing(false);
        } else if (attempts >= maxAttempts) {
          // Timeout
          setError('Payment confirmation timeout. Please try again.');
          setIsProcessing(false);
        } else {
          // Continue polling
          setTimeout(poll, 10000); // Check every 10 seconds
        }
      } catch (err) {
        logError(err, 'Payment status polling', 'error');
        setError('Error checking payment status');
        setIsProcessing(false);
      }
    };
    
    poll();
  };

  const simulatePaymentStatusCheck = async (checkoutRequestId) => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Simulate successful payment after 3 attempts
    const attempts = parseInt(localStorage.getItem('payment_attempts') || '0');
    localStorage.setItem('payment_attempts', (attempts + 1).toString());
    
    if (attempts >= 2) {
      localStorage.removeItem('payment_attempts');
      return { resultCode: '0', resultDesc: 'The service request is processed successfully.' };
    }
    
    return { resultCode: 'pending', resultDesc: 'Payment pending' };
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (userCredits <= 0) {
        setShowPayment(true);
        setError('No credits remaining. Please purchase credits to continue.');
        return;
      }
      
      setUploadedFile(file);
      setCurrentStep('processing');
      setError('');
      processFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      if (userCredits <= 0) {
        setShowPayment(true);
        setError('No credits remaining. Please purchase credits to continue.');
        return;
      }
      
      setUploadedFile(file);
      setCurrentStep('processing');
      setError('');
      processFile(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const processFile = async (file) => {
    setIsProcessing(true);
    try {
      // Deduct one credit
      saveCredits(userCredits - 1);
      
      // Check if it's an image file for OCR processing
      if (file.type.startsWith('image/') || file.type === 'application/pdf') {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('https://invoice-extractor-cso1.onrender.com/api/ocr', {
          method: 'POST',
          body: formData,
        });
        const data = await response.json();
        setExtractedText(data.text);
        await extractStructuredData(data.text);
      } else {
        throw new Error('Unsupported file type. Please upload PDF or image files.');
      }
    } catch (err) {
      logError(err, 'File processing', 'error');
      // Refund credit on error
      saveCredits(userCredits);
      setError(err.message);
      setCurrentStep('upload');
      setIsProcessing(false);
    }
  };

  const extractStructuredData = async (text) => {
    try {
      // Use Claude API to extract structured data
      const prompt = `
      Extract invoice data from the following text and return it as a JSON object with these exact field names:
      - "Invoice Number"
      - "Invoice Date"
      - "Vendor Name"
      - "Vendor Address"
      - "Total Amount"
      - "Tax Amount"
      - "Subtotal"
      - "Due Date"
      - "Purchase Order"
      - "Description"
      
      If a field is not found, use empty string. For amounts, include only the number without currency symbols.
      
      Text to extract from:
      ${text}
      
      Respond with ONLY a valid JSON object, no other text.
      `;

      const response = await window.claude.complete(prompt);
      const parsedData = JSON.parse(response);
      
      setExtractedData(parsedData);
      setCurrentStep('review');
      setIsProcessing(false);
    } catch (err) {
      logError(err, 'Data extraction via Claude API', 'warning');
      console.error('Error extracting data:', err);
      // Fallback to manual parsing if Claude API fails
      const fallbackData = manualExtraction(text);
      setExtractedData(fallbackData);
      setCurrentStep('review');
      setIsProcessing(false);
    }
  };

  const manualExtraction = (text) => {
    try {
      // Simple regex-based extraction as fallback
      const invoiceNumber = text.match(/(?:Invoice|INV)[\s#:]*([A-Z0-9-]+)/i)?.[1] || '';
      const date = text.match(/Date:\s*([^\n]+)/i)?.[1] || '';
      const total = text.match(/Total:\s*\$?([0-9,]+\.?[0-9]*)/i)?.[1] || '';
      const vendor = text.match(/^([^\n]+Corporation|[^\n]+Company|[^\n]+Inc)/m)?.[1] || '';
      
      return {
        "Invoice Number": invoiceNumber,
        "Invoice Date": date,
        "Vendor Name": vendor,
        "Vendor Address": "",
        "Total Amount": total,
        "Tax Amount": "",
        "Subtotal": "",
        "Due Date": "",
        "Purchase Order": "",
        "Description": ""
      };
    } catch (err) {
      logError(err, 'Manual data extraction', 'warning');
      return {};
    }
  };

  const handleFieldChange = (field, value) => {
    setExtractedData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const sendToGoogleSheets = async () => {
    if (!googleSheetsUrl) {
      setError('Please enter a Google Sheets URL');
      return;
    }

    setIsProcessing(true);
    try {
      // Simulate sending to Google Sheets
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setSuccessMessage('Data successfully sent to Google Sheets!');
      setCurrentStep('success');
      
      // Log successful processing
      logError({message: 'Invoice successfully processed and sent to Google Sheets'}, 'processing_success', 'info');
      
    } catch (err) {
      logError(err, 'Google Sheets integration', 'error');
      setError('Failed to send data to Google Sheets. Please check your URL and try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const resetApp = () => {
    setCurrentStep('upload');
    setUploadedFile(null);
    setExtractedText('');
    setExtractedData(null);
    setError('');
    setSuccessMessage('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const renderPaymentModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
        <div className="text-center mb-6">
          <Smartphone className="mx-auto h-12 w-12 text-green-600 mb-4" />
          <h3 className="text-xl font-bold mb-2">Purchase Credits</h3>
          <p className="text-gray-600">
            Credits remaining: <span className="font-semibold text-red-600">{userCredits}</span>
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              M-Pesa Phone Number
            </label>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="254712345678"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter number in format: 254XXXXXXXXX
            </p>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium mb-2">Credit Packages:</h4>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="package"
                  value="50"
                  checked={paymentAmount === 50}
                  onChange={(e) => setPaymentAmount(parseInt(e.target.value))}
                  className="mr-2"
                />
                <span>KES 50 - 5 Credits (KES 10 per invoice)</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="package"
                  value="200"
                  checked={paymentAmount === 200}
                  onChange={(e) => setPaymentAmount(parseInt(e.target.value))}
                  className="mr-2"
                />
                <span>KES 200 - 25 Credits (KES 8 per invoice) - Save 20%</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="package"
                  value="500"
                  checked={paymentAmount === 500}
                  onChange={(e) => setPaymentAmount(parseInt(e.target.value))}
                  className="mr-2"
                />
                <span>KES 500 - 75 Credits (KES 6.67 per invoice) - Save 33%</span>
              </label>
            </div>
          </div>

          {paymentStatus && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <div className="flex items-center">
                <Clock className="h-5 w-5 text-blue-600 mr-2" />
                <span className="text-blue-700 text-sm">{paymentStatus}</span>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={initiateMpesaPayment}
              disabled={isProcessing}
              className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Smartphone className="h-4 w-4" />
              {isProcessing ? 'Processing...' : `Pay KES ${paymentAmount}`}
            </button>
            <button
              onClick={() => setShowPayment(false)}
              disabled={isProcessing}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderErrorLogs = () => (
    <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <AlertTriangle className="h-5 w-5 text-orange-500" />
        Error Documentation
      </h3>
      {errorLogs.length === 0 ? (
        <p className="text-gray-500">No errors logged</p>
      ) : (
        <div className="space-y-3 max-h-60 overflow-y-auto">
          {errorLogs.map(log => (
            <div key={log.id} className={`p-3 rounded-md border ${
              log.severity === 'error' ? 'bg-red-50 border-red-200' :
              log.severity === 'warning' ? 'bg-yellow-50 border-yellow-200' :
              'bg-blue-50 border-blue-200'
            }`}>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className={`text-sm font-medium ${
                    log.severity === 'error' ? 'text-red-800' :
                    log.severity === 'warning' ? 'text-yellow-800' :
                    'text-blue-800'
                  }`}>
                    {log.error}
                  </p>
                  {log.context && (
                    <p className="text-xs text-gray-600 mt-1">Context: {log.context}</p>
                  )}
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderUploadStep = () => (
    <div className="text-center">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-green-600" />
          <span className="text-sm font-medium">Credits: {userCredits}</span>
        </div>
        <button
          onClick={() => setShowPayment(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center gap-2"
        >
          <CreditCard className="h-4 w-4" />
          Buy Credits
        </button>
      </div>
      
      <div 
        className="border-2 border-dashed border-blue-300 rounded-lg p-12 hover:border-blue-400 transition-colors cursor-pointer"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload className="mx-auto h-16 w-16 text-blue-400 mb-4" />
        <h3 className="text-xl font-semibold mb-2">Upload Invoice</h3>
        <p className="text-gray-600 mb-4">
          Drag and drop your invoice file here, or click to browse
        </p>
        <p className="text-sm text-gray-500">
          Supports PDF, JPG, PNG formats • Costs 1 credit per invoice
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>
    </div>
  );

  const renderProcessingStep = () => (
    <div className="text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
      <h3 className="text-xl font-semibold mb-2">Processing Invoice</h3>
      <p className="text-gray-600">
        Extracting text and identifying data fields...
      </p>
      <p className="text-sm text-gray-500 mt-2">
        Credits remaining: {userCredits}
      </p>
    </div>
  );

  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold">Review Extracted Data</h3>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">Credits: {userCredits}</span>
          <button
            onClick={() => setCurrentStep('text')}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-700"
          >
            <Eye className="h-4 w-4" />
            View Raw Text
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {standardFields.map(field => (
          <div key={field}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {field}
            </label>
            <input
              type="text"
              value={extractedData?.[field] || ''}
              onChange={(e) => handleFieldChange(field, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={`Enter ${field.toLowerCase()}`}
            />
          </div>
        ))}
      </div>

      <div className="border-t pt-6">
        <h4 className="text-lg font-medium mb-3">Google Sheets Integration</h4>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Google Sheets URL
          </label>
          <input
            type="url"
            value={googleSheetsUrl}
            onChange={(e) => setGoogleSheetsUrl(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="https://docs.google.com/spreadsheets/d/..."
          />
          <p className="text-xs text-gray-500 mt-1">
            Make sure the sheet is publicly accessible or you have proper permissions
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={sendToGoogleSheets}
            disabled={isProcessing}
            className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Send className="h-4 w-4" />
            {isProcessing ? 'Sending...' : 'Send to Google Sheets'}
          </button>
          <button
            onClick={resetApp}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );

  const renderTextStep = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold">Extracted Text</h3>
        <button
          onClick={() => setCurrentStep('review')}
          className="text-blue-600 hover:text-blue-700"
        >
          Back to Review
        </button>
      </div>
      <div className="bg-gray-50 p-4 rounded-lg">
        <pre className="whitespace-pre-wrap text-sm text-gray-700">
          {extractedText}
        </pre>
      </div>
    </div>
  );

  const renderSuccessStep = () => (
    <div className="text-center">
      <CheckCircle className="mx-auto h-16 w-16 text-green-500 mb-4" />
      <h3 className="text-xl font-semibold mb-2">Success!</h3>
      <p className="text-gray-600 mb-4">
        Invoice data has been successfully extracted and sent to your Google Sheet.
      </p>
      <p className="text-sm text-gray-500 mb-6">
        Credits remaining: {userCredits}
      </p>
      <div className="flex gap-3 justify-center">
        <button
          onClick={resetApp}
          className="bg-blue-600 text-white py-2 px-6 rounded-md hover:bg-blue-700"
        >
          Process Another Invoice
        </button>
        <button
          onClick={() => setShowPayment(true)}
          className="bg-green-600 text-white py-2 px-6 rounded-md hover:bg-green-700"
        >
          Buy More Credits
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Invoice Data Extractor
          </h1>
          <p className="text-gray-600">
            Upload invoices, extract data with OCR, and send to Google Sheets
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center space-x-4">
            {[
              { key: 'upload', label: 'Upload', icon: Upload },
              { key: 'processing', label: 'Process', icon: Settings },
              { key: 'review', label: 'Review', icon: Eye },
              { key: 'success', label: 'Complete', icon: CheckCircle }
            ].map(({ key, label, icon: Icon }, index) => (
              <div key={key} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                  currentStep === key ? 'bg-blue-600 text-white' :
                  ['review', 'success'].includes(currentStep) && ['upload', 'processing'].includes(key) ? 'bg-green-600 text-white' :
                  currentStep === 'success' && key === 'review' ? 'bg-green-600 text-white' :
                  'bg-gray-300 text-gray-600'
                }`}>
                  <Icon className="h-5 w-5" />
                </div>
                <span className="ml-2 text-sm font-medium">{label}</span>
                {index < 3 && <div className="w-8 h-px bg-gray-300 mx-4" />}
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          {currentStep === 'upload' && renderUploadStep()}
          {currentStep === 'processing' && renderProcessingStep()}
          {currentStep === 'review' && renderReviewStep()}
          {currentStep === 'text' && renderTextStep()}
          {currentStep === 'success' && renderSuccessStep()}
        </div>

        {/* Info Section */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">How it works:</h3>
          <ol className="text-blue-800 space-y-1 text-sm">
            <li>1. Purchase credits via M-Pesa (KES 10 per invoice)</li>
            <li>2. Upload your invoice (PDF or image format)</li>
            <li>3. OCR technology extracts text from the document</li>
            <li>4. AI intelligently identifies and maps invoice fields</li>
            <li>5. Review and edit the extracted data</li>
            <li>6. Send the structured data directly to your Google Sheet</li>
          </ol>
        </div>

        {/* Payment Modal */}
        {showPayment && renderPaymentModal()}

        {/* Error Documentation */}
        {renderErrorLogs()}
      </div>
    </div>
  );
};

//export default InvoiceExtractor;